"""Resolution generation node - creates customer-ready responses with citations."""

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime

from app.agents.state import AgentState, Citation
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


RESOLUTION_GENERATION_PROMPT = """You are an expert customer service assistant for Fidelity Investments.

Your task is to generate a clear, accurate, and helpful response to a customer's question based on search results from fidelity.com and internal documentation.

## Customer Query:
{query}

## Search Results:
{search_results}

## Previous Feedback (if any):
{feedback}

## Instructions:
1. Analyze all search results carefully
2. Synthesize information from multiple sources
3. Create a clear, customer-friendly response that directly addresses the query
4. Include specific citations for every factual claim using the format: [Source: URL]
5. Keep the response concise but complete (2-4 paragraphs)
6. Use professional but friendly language
7. If the search results don't contain enough information, acknowledge this

## Response Guidelines:
- Start with a direct answer to the customer's question
- Provide step-by-step instructions if applicable
- Include relevant warnings or important notes
- End with additional resources or next steps if helpful
- ALWAYS cite your sources inline

## Citation Format:
When making a factual claim, immediately cite the source:
"According to Fidelity's help documentation [Source: https://fidelity.com/help/...], you can..."

Generate the customer response below:
"""


def resolution_generation_node(state: AgentState) -> AgentState:
    """
    Generate customer-ready resolution with citations.

    This node:
    1. Takes search results and query
    2. Uses LLM to synthesize information
    3. Generates response with inline citations
    4. Extracts citation metadata

    Args:
        state: Current agent state with query and search_results

    Returns:
        Updated state with resolution_text and citations
    """
    query = state.get("optimized_query", "")
    search_results = state.get("search_results", [])
    feedback_history = state.get("feedback_history", [])

    if not query:
        logger.error("No query available for resolution generation")
        state["error_message"] = "No query provided"
        return state

    if not search_results:
        logger.warning("No search results available for resolution generation")
        state["resolution_text"] = (
            "I apologize, but I couldn't find specific information to answer your question. "
            "For immediate assistance, please contact Fidelity customer service at 1-800-FIDELITY (1-800-343-3548)."
        )
        state["citations"] = []
        return state

    logger.info(f"Generating resolution for query: '{query}' with {len(search_results)} search results")

    try:
        # Initialize LLM
        llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            deployment_name=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            temperature=0.5,  # Balanced between creativity and consistency
            max_tokens=settings.AZURE_OPENAI_MAX_TOKENS,
        )

        # Format search results
        formatted_results = []
        for idx, result in enumerate(search_results, 1):
            formatted_results.append(
                f"[{idx}] {result['title']}\n"
                f"    URL: {result['url']}\n"
                f"    Source: {result['source']}\n"
                f"    Content: {result['content'][:500]}...\n"
            )

        search_results_text = "\n".join(formatted_results)
        feedback_text = "\n".join(feedback_history) if feedback_history else "None"

        # Create prompt
        prompt = ChatPromptTemplate.from_template(RESOLUTION_GENERATION_PROMPT)

        # Create chain
        chain = prompt | llm | StrOutputParser()

        # Generate resolution
        resolution = chain.invoke({
            "query": query,
            "search_results": search_results_text,
            "feedback": feedback_text
        })

        # Extract citations from the resolution text
        citations = _extract_citations(resolution, search_results)

        # Update state
        state["resolution_text"] = resolution
        state["citations"] = citations
        state["generation_timestamp"] = datetime.utcnow()

        logger.info(
            f"Resolution generated successfully. "
            f"Length: {len(resolution)} chars, Citations: {len(citations)}"
        )

        return state

    except Exception as e:
        logger.exception(f"Resolution generation failed: {str(e)}")
        state["error_message"] = f"Resolution generation error: {str(e)}"

        # Provide fallback response
        state["resolution_text"] = (
            "I apologize, but I'm having trouble generating a response at the moment. "
            "For immediate assistance, please contact Fidelity customer service at 1-800-FIDELITY (1-800-343-3548)."
        )
        state["citations"] = []

        return state


def _extract_citations(text: str, search_results: list) -> list[Citation]:
    """
    Extract citation metadata from resolution text.

    Looks for [Source: URL] patterns and matches them to search results.
    """
    import re

    citations = []
    seen_urls = set()

    # Pattern to match citations in text
    citation_pattern = r'\[Source:\s*(https?://[^\]]+)\]'

    # Find all citations
    for match in re.finditer(citation_pattern, text):
        url = match.group(1).strip()

        if url in seen_urls:
            continue

        seen_urls.add(url)

        # Try to find matching search result for additional context
        matching_result = None
        for result in search_results:
            if result["url"] == url:
                matching_result = result
                break

        if matching_result:
            citations.append(Citation(
                source=matching_result.get("title", "Fidelity Documentation"),
                url=url,
                snippet=matching_result.get("content", "")[:200],
                confidence=matching_result.get("relevance_score", 0.8)
            ))
        else:
            # Citation found but no matching search result
            citations.append(Citation(
                source="Fidelity Documentation",
                url=url,
                snippet="",
                confidence=0.7
            ))

    logger.info(f"Extracted {len(citations)} citations from resolution")
    return citations


# Export for use in workflow
__all__ = ["resolution_generation_node"]
