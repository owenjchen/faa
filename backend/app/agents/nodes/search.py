"""Search node - performs parallel searches across fidelity.com and myGPS."""

import asyncio
from typing import List, Dict, Any
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from trafilatura import extract
from urllib.parse import quote_plus, urljoin

from app.agents.state import AgentState, SearchResult
from app.config import settings
from app.utils.logging import get_logger
from app.core.vector_store import get_vector_store

logger = get_logger(__name__)


class FidelitySearcher:
    """
    Search fidelity.com using web scraping and content extraction.

    Implements multiple search strategies:
    1. Google site search (most reliable)
    2. Fidelity native search
    3. Vector similarity search in cached content
    """

    def __init__(self):
        self.base_url = settings.FIDELITY_SEARCH_URL
        self.timeout = settings.SEARCH_TIMEOUT
        self.top_k = settings.SEARCH_TOP_K

    async def search(self, query: str, k: int = None) -> List[SearchResult]:
        """
        Execute search on fidelity.com.

        Args:
            query: Search query string
            k: Number of results to return (defaults to settings.SEARCH_TOP_K)

        Returns:
            List of search results with content and metadata
        """
        k = k or self.top_k
        logger.info(f"Searching fidelity.com for: '{query}' (top {k})")

        try:
            # Try multiple search strategies in parallel
            results = await asyncio.gather(
                self._google_site_search(query, k),
                self._fidelity_native_search(query, k),
                return_exceptions=True
            )

            # Combine and deduplicate results
            all_results = []
            seen_urls = set()

            for result_set in results:
                if isinstance(result_set, Exception):
                    logger.warning(f"Search method failed: {str(result_set)}")
                    continue

                for result in result_set:
                    if result["url"] not in seen_urls:
                        all_results.append(result)
                        seen_urls.add(result["url"])

            # Sort by relevance score and limit to k
            all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            final_results = all_results[:k]

            logger.info(f"Found {len(final_results)} unique results from fidelity.com")
            return final_results

        except Exception as e:
            logger.exception(f"Fidelity search failed: {str(e)}")
            return []

    async def _google_site_search(self, query: str, k: int) -> List[SearchResult]:
        """
        Use Google to search within fidelity.com.

        Most reliable method as it leverages Google's search index.
        """
        try:
            # Construct Google site search query
            site_query = f"site:fidelity.com {query}"
            google_url = f"https://www.google.com/search?q={quote_plus(site_query)}&num={k}"

            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                # Add headers to avoid being blocked
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                }

                response = await client.get(google_url, headers=headers)
                response.raise_for_status()

            # Parse Google search results
            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            # Extract search result links
            for result_div in soup.select("div.g")[:k]:
                try:
                    link_tag = result_div.select_one("a")
                    title_tag = result_div.select_one("h3")
                    snippet_tag = result_div.select_one("div[data-content-feature='1']")

                    if not link_tag or not title_tag:
                        continue

                    url = link_tag.get("href", "")
                    if not url.startswith("http"):
                        continue

                    title = title_tag.get_text(strip=True)
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

                    # Fetch and extract full content
                    content = await self._fetch_page_content(url)

                    results.append(SearchResult(
                        source="fidelity",
                        title=title,
                        url=url,
                        content=content or snippet,
                        relevance_score=0.9 - (len(results) * 0.05)  # Descending score
                    ))

                except Exception as e:
                    logger.warning(f"Failed to parse Google result: {str(e)}")
                    continue

            logger.info(f"Google site search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Google site search failed: {str(e)}")
            return []

    async def _fidelity_native_search(self, query: str, k: int) -> List[SearchResult]:
        """
        Use Fidelity's native search endpoint if available.

        Fallback method if Google search fails.
        """
        try:
            # Fidelity search endpoint (adjust based on actual endpoint)
            search_url = f"{self.base_url}/search"
            params = {
                "query": query,
                "limit": k
            }

            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json,text/html",
                }

                response = await client.get(search_url, params=params, headers=headers)
                response.raise_for_status()

            # Try to parse as JSON first
            try:
                data = response.json()
                results = self._parse_fidelity_json_results(data, k)
            except Exception:
                # Fall back to HTML parsing
                results = self._parse_fidelity_html_results(response.text, k)

            logger.info(f"Fidelity native search returned {len(results)} results")
            return results

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info("Fidelity native search endpoint not found, skipping")
            else:
                logger.error(f"Fidelity native search failed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Fidelity native search failed: {str(e)}")
            return []

    async def _fetch_page_content(self, url: str) -> str:
        """
        Fetch and extract clean text content from a webpage.

        Uses trafilatura for high-quality content extraction.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                }
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            # Extract main content using trafilatura
            content = extract(
                response.text,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )

            if content:
                # Limit content length to avoid token overflow
                max_length = 2000
                if len(content) > max_length:
                    content = content[:max_length] + "..."

                return content

            # Fallback to BeautifulSoup if trafilatura fails
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text and clean it
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            # Limit length
            if len(text) > max_length:
                text = text[:max_length] + "..."

            return text

        except Exception as e:
            logger.warning(f"Failed to fetch content from {url}: {str(e)}")
            return ""

    def _parse_fidelity_json_results(self, data: Dict[str, Any], k: int) -> List[SearchResult]:
        """Parse JSON response from Fidelity search API."""
        results = []

        # Adjust field names based on actual API response structure
        items = data.get("results", data.get("items", []))[:k]

        for idx, item in enumerate(items):
            results.append(SearchResult(
                source="fidelity",
                title=item.get("title", ""),
                url=item.get("url", item.get("link", "")),
                content=item.get("content", item.get("snippet", "")),
                relevance_score=item.get("score", 0.8 - (idx * 0.05))
            ))

        return results

    def _parse_fidelity_html_results(self, html: str, k: int) -> List[SearchResult]:
        """Parse HTML search results page."""
        soup = BeautifulSoup(html, "html.parser")
        results = []

        # Look for common search result patterns
        # Adjust selectors based on actual Fidelity HTML structure
        result_containers = soup.select("div.search-result, article.result, div.result-item")[:k]

        for idx, container in enumerate(result_containers):
            try:
                title_tag = container.select_one("h2, h3, a.title")
                link_tag = container.select_one("a")
                snippet_tag = container.select_one("p, div.snippet, div.description")

                if not title_tag or not link_tag:
                    continue

                title = title_tag.get_text(strip=True)
                url = link_tag.get("href", "")

                # Handle relative URLs
                if url and not url.startswith("http"):
                    url = urljoin(self.base_url, url)

                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

                results.append(SearchResult(
                    source="fidelity",
                    title=title,
                    url=url,
                    content=snippet,
                    relevance_score=0.7 - (idx * 0.05)
                ))

            except Exception as e:
                logger.warning(f"Failed to parse HTML result: {str(e)}")
                continue

        return results


class MyGPSSearcher:
    """
    Search internal myGPS content.

    Requires authentication and API access.
    """

    def __init__(self):
        self.api_url = settings.MYGPS_API_URL
        self.api_key = settings.MYGPS_API_KEY
        self.timeout = settings.SEARCH_TIMEOUT
        self.top_k = settings.SEARCH_TOP_K

    async def search(self, query: str, k: int = None) -> List[SearchResult]:
        """
        Execute search on myGPS internal content.

        Args:
            query: Search query string
            k: Number of results to return

        Returns:
            List of search results from internal content
        """
        if not self.api_url or not self.api_key:
            logger.warning("myGPS API not configured, skipping internal search")
            return []

        k = k or self.top_k
        logger.info(f"Searching myGPS for: '{query}' (top {k})")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                payload = {
                    "query": query,
                    "limit": k,
                    "include_content": True
                }

                response = await client.post(
                    f"{self.api_url}/search",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()

            data = response.json()
            results = []

            for idx, item in enumerate(data.get("results", [])[:k]):
                results.append(SearchResult(
                    source="mygps",
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", item.get("snippet", "")),
                    relevance_score=item.get("score", 0.9 - (idx * 0.05))
                ))

            logger.info(f"myGPS search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"myGPS search failed: {str(e)}")
            return []


async def parallel_search_node(state: AgentState) -> AgentState:
    """
    Execute parallel searches across fidelity.com and myGPS.

    This node:
    1. Searches fidelity.com using multiple strategies
    2. Searches myGPS internal content (if configured)
    3. Optionally searches cached vector store
    4. Combines and ranks all results

    Args:
        state: Current agent state with optimized_query

    Returns:
        Updated state with search_results
    """
    query = state.get("optimized_query", "")

    if not query:
        logger.error("No query provided for search")
        state["search_errors"].append("No search query available")
        return state

    logger.info(f"Starting parallel search for query: '{query}'")

    # Initialize searchers
    fidelity_searcher = FidelitySearcher()
    mygps_searcher = MyGPSSearcher()

    # Execute searches in parallel
    search_tasks = [
        fidelity_searcher.search(query, k=settings.SEARCH_TOP_K),
        mygps_searcher.search(query, k=settings.SEARCH_TOP_K),
    ]

    # Add vector store search if available
    try:
        vector_store = get_vector_store()
        search_tasks.append(
            asyncio.to_thread(
                vector_store.similarity_search,
                query,
                k=settings.SEARCH_TOP_K
            )
        )
    except Exception as e:
        logger.warning(f"Vector store not available: {str(e)}")

    # Execute all searches
    try:
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
    except Exception as e:
        logger.exception(f"Parallel search failed: {str(e)}")
        state["search_errors"].append(f"Search execution error: {str(e)}")
        return state

    # Combine results
    all_results = []
    for idx, result_set in enumerate(results):
        if isinstance(result_set, Exception):
            logger.error(f"Search task {idx} failed: {str(result_set)}")
            state["search_errors"].append(f"Search source {idx} failed: {str(result_set)}")
            continue

        # Handle both SearchResult objects and dict results from vector store
        for result in result_set:
            if isinstance(result, dict):
                # Convert vector store results to SearchResult
                all_results.append(SearchResult(
                    source=result.get("source", "vector_store"),
                    title=result.get("title", ""),
                    url=result.get("url", ""),
                    content=result.get("content", ""),
                    relevance_score=result.get("score", 0.5)
                ))
            else:
                all_results.append(result)

    # Deduplicate by URL
    seen_urls = set()
    unique_results = []
    for result in all_results:
        if result["url"] not in seen_urls:
            unique_results.append(result)
            seen_urls.add(result["url"])

    # Sort by relevance score
    unique_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    # Limit to top K across all sources
    final_results = unique_results[:settings.SEARCH_TOP_K * 2]  # Get 2x for diversity

    state["search_results"] = final_results

    logger.info(
        f"Parallel search completed: {len(final_results)} unique results "
        f"(fidelity: {sum(1 for r in final_results if r['source'] == 'fidelity')}, "
        f"mygps: {sum(1 for r in final_results if r['source'] == 'mygps')})"
    )

    # Log if no results found
    if not final_results:
        logger.warning(f"No search results found for query: '{query}'")
        state["search_errors"].append("No search results found")

    return state


# Export for use in workflow
__all__ = ["parallel_search_node", "FidelitySearcher", "MyGPSSearcher"]
