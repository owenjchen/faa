"""OpenSearch vector store integration for semantic search."""

from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class OpenSearchVectorStore:
    """
    OpenSearch vector store for semantic search and retrieval.

    Supports:
    - Vector similarity search with k-NN
    - Hybrid search (vector + keyword)
    - Document indexing with embeddings
    - Metadata filtering
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: Optional[bool] = None,
        verify_certs: Optional[bool] = None,
        index_name: Optional[str] = None,
    ):
        """
        Initialize OpenSearch client.

        Args:
            host: OpenSearch endpoint (defaults to settings)
            port: OpenSearch port (defaults to settings)
            username: Authentication username
            password: Authentication password
            use_ssl: Use SSL connection
            verify_certs: Verify SSL certificates
            index_name: Name of the index to use
        """
        self.host = host or settings.OPENSEARCH_HOST
        self.port = port or settings.OPENSEARCH_PORT
        self.username = username or settings.OPENSEARCH_USERNAME
        self.password = password or settings.OPENSEARCH_PASSWORD
        self.use_ssl = use_ssl if use_ssl is not None else settings.OPENSEARCH_USE_SSL
        self.verify_certs = verify_certs if verify_certs is not None else settings.OPENSEARCH_VERIFY_CERTS
        self.index_name = index_name or settings.OPENSEARCH_INDEX_NAME

        self.vector_field = settings.OPENSEARCH_VECTOR_FIELD
        self.text_field = settings.OPENSEARCH_TEXT_FIELD
        self.metadata_field = settings.OPENSEARCH_METADATA_FIELD

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.embedding_dimension = settings.EMBEDDING_DIMENSION

        # Initialize OpenSearch client
        self.client = self._create_client()

        logger.info(f"OpenSearch vector store initialized with index: {self.index_name}")

    def _create_client(self) -> OpenSearch:
        """Create OpenSearch client with appropriate authentication."""

        if not self.host:
            raise ValueError("OpenSearch host must be configured")

        # Check if using AWS authentication (no username/password means IAM)
        if not self.username and not self.password:
            # Use AWS IAM authentication
            credentials = boto3.Session(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            ).get_credentials()

            awsauth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                settings.AWS_REGION,
                'es',  # OpenSearch uses 'es' service name
                session_token=credentials.token
            )

            client = OpenSearch(
                hosts=[{'host': self.host, 'port': self.port}],
                http_auth=awsauth,
                use_ssl=self.use_ssl,
                verify_certs=self.verify_certs,
                connection_class=RequestsHttpConnection,
                timeout=30,
            )
            logger.info("Using AWS IAM authentication for OpenSearch")
        else:
            # Use basic authentication
            client = OpenSearch(
                hosts=[{'host': self.host, 'port': self.port}],
                http_auth=(self.username, self.password),
                use_ssl=self.use_ssl,
                verify_certs=self.verify_certs,
                connection_class=RequestsHttpConnection,
                timeout=30,
            )
            logger.info("Using basic authentication for OpenSearch")

        return client

    def create_index(self, force: bool = False) -> bool:
        """
        Create OpenSearch index with k-NN configuration.

        Args:
            force: Delete existing index if it exists

        Returns:
            True if index was created, False if already exists
        """
        if self.client.indices.exists(index=self.index_name):
            if force:
                logger.warning(f"Deleting existing index: {self.index_name}")
                self.client.indices.delete(index=self.index_name)
            else:
                logger.info(f"Index {self.index_name} already exists")
                return False

        # Index configuration with k-NN
        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 512,
                    "number_of_shards": 2,
                    "number_of_replicas": 1,
                }
            },
            "mappings": {
                "properties": {
                    self.text_field: {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    self.vector_field: {
                        "type": "knn_vector",
                        "dimension": self.embedding_dimension,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 512,
                                "m": 16
                            }
                        }
                    },
                    self.metadata_field: {
                        "type": "object",
                        "enabled": True
                    },
                    "id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "url": {"type": "keyword"},
                    "title": {"type": "text"},
                    "created_at": {"type": "date"}
                }
            }
        }

        self.client.indices.create(index=self.index_name, body=index_body)
        logger.info(f"Created index: {self.index_name}")
        return True

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Add documents to the vector store.

        Args:
            texts: List of text documents to index
            metadatas: Optional metadata for each document
            ids: Optional custom IDs for documents

        Returns:
            List of document IDs
        """
        if metadatas is None:
            metadatas = [{} for _ in texts]

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} documents")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)

        # Index documents
        doc_ids = []
        for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
            doc_id = ids[i] if ids and i < len(ids) else f"doc_{i}_{hash(text)}"

            document = {
                self.text_field: text,
                self.vector_field: embedding.tolist(),
                self.metadata_field: metadata,
                "id": doc_id,
            }

            # Add optional fields from metadata
            if "source" in metadata:
                document["source"] = metadata["source"]
            if "url" in metadata:
                document["url"] = metadata["url"]
            if "title" in metadata:
                document["title"] = metadata["title"]

            self.client.index(
                index=self.index_name,
                id=doc_id,
                body=document,
                refresh=True
            )
            doc_ids.append(doc_id)

        logger.info(f"Indexed {len(doc_ids)} documents")
        return doc_ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.

        Args:
            query: Search query text
            k: Number of results to return
            filter_dict: Optional metadata filters

        Returns:
            List of matching documents with scores
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)

        # Build k-NN query
        knn_query = {
            "size": k,
            "query": {
                "knn": {
                    self.vector_field: {
                        "vector": query_embedding.tolist(),
                        "k": k
                    }
                }
            },
            "_source": [self.text_field, self.metadata_field, "source", "url", "title"]
        }

        # Add filters if provided
        if filter_dict:
            knn_query["query"] = {
                "bool": {
                    "must": [knn_query["query"]],
                    "filter": [
                        {"term": {f"{self.metadata_field}.{key}": value}}
                        for key, value in filter_dict.items()
                    ]
                }
            }

        # Execute search
        response = self.client.search(
            index=self.index_name,
            body=knn_query
        )

        # Format results
        results = []
        for hit in response['hits']['hits']:
            results.append({
                "id": hit["_id"],
                "score": hit["_score"],
                "content": hit["_source"].get(self.text_field, ""),
                "metadata": hit["_source"].get(self.metadata_field, {}),
                "source": hit["_source"].get("source"),
                "url": hit["_source"].get("url"),
                "title": hit["_source"].get("title"),
            })

        logger.info(f"Found {len(results)} results for query: '{query[:50]}...'")
        return results

    def hybrid_search(
        self,
        query: str,
        k: int = 5,
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining keyword and vector search.

        Args:
            query: Search query text
            k: Number of results to return
            keyword_weight: Weight for keyword search (0-1)
            vector_weight: Weight for vector search (0-1)
            filter_dict: Optional metadata filters

        Returns:
            List of matching documents with combined scores
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)

        # Build hybrid query
        hybrid_query = {
            "size": k,
            "query": {
                "bool": {
                    "should": [
                        # Vector similarity
                        {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": f"knn_score",
                                    "lang": "knn",
                                    "params": {
                                        "field": self.vector_field,
                                        "query_value": query_embedding.tolist(),
                                        "space_type": "cosinesimil"
                                    }
                                },
                                "boost": vector_weight
                            }
                        },
                        # Keyword search
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [self.text_field, "title^2"],
                                "boost": keyword_weight
                            }
                        }
                    ]
                }
            },
            "_source": [self.text_field, self.metadata_field, "source", "url", "title"]
        }

        # Add filters if provided
        if filter_dict:
            hybrid_query["query"]["bool"]["filter"] = [
                {"term": {f"{self.metadata_field}.{key}": value}}
                for key, value in filter_dict.items()
            ]

        # Execute search
        response = self.client.search(
            index=self.index_name,
            body=hybrid_query
        )

        # Format results
        results = []
        for hit in response['hits']['hits']:
            results.append({
                "id": hit["_id"],
                "score": hit["_score"],
                "content": hit["_source"].get(self.text_field, ""),
                "metadata": hit["_source"].get(self.metadata_field, {}),
                "source": hit["_source"].get("source"),
                "url": hit["_source"].get("url"),
                "title": hit["_source"].get("title"),
            })

        logger.info(f"Hybrid search found {len(results)} results")
        return results

    def delete_index(self) -> bool:
        """Delete the index."""
        if self.client.indices.exists(index=self.index_name):
            self.client.indices.delete(index=self.index_name)
            logger.info(f"Deleted index: {self.index_name}")
            return True
        return False

    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        stats = self.client.indices.stats(index=self.index_name)
        return {
            "document_count": stats["indices"][self.index_name]["total"]["docs"]["count"],
            "size_bytes": stats["indices"][self.index_name]["total"]["store"]["size_in_bytes"],
        }


# Global vector store instance
_vector_store: Optional[OpenSearchVectorStore] = None


def get_vector_store() -> OpenSearchVectorStore:
    """Get or create the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = OpenSearchVectorStore()
    return _vector_store
