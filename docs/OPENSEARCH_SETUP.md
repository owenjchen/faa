# OpenSearch Setup and Configuration

This document describes how to configure and use AWS OpenSearch as the vector store for the Fidelity Agent Assistant.

## Overview

FAA uses AWS OpenSearch for:
- **Vector similarity search** using k-NN (k-nearest neighbors)
- **Hybrid search** combining keyword and semantic search
- **Document storage** with embeddings and metadata
- **Scalable retrieval** for fidelity.com and myGPS content

## Prerequisites

An AWS OpenSearch instance must already be created and configured. Contact your AWS administrator if you don't have access.

## Configuration

### Environment Variables

Add these to `backend/.env`:

```bash
# OpenSearch Configuration (Required)
OPENSEARCH_HOST=search-faa-xxxxx.us-east-1.es.amazonaws.com
OPENSEARCH_PORT=443
OPENSEARCH_USE_SSL=true
OPENSEARCH_VERIFY_CERTS=true
OPENSEARCH_INDEX_NAME=faa_knowledge_base

# AWS Credentials (for IAM authentication)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key

# Optional: Basic Auth (if not using IAM)
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=your_password

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

## Authentication

### IAM Authentication (Recommended)

If `OPENSEARCH_USERNAME` and `OPENSEARCH_PASSWORD` are not set, the system will automatically use AWS IAM authentication with the provided AWS credentials.

**Required IAM Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "es:ESHttpGet",
        "es:ESHttpPost",
        "es:ESHttpPut",
        "es:ESHttpDelete"
      ],
      "Resource": "arn:aws:es:us-east-1:ACCOUNT_ID:domain/faa-opensearch/*"
    }
  ]
}
```

### Basic Authentication

If your OpenSearch cluster uses basic authentication:

```bash
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=YourStrongPassword123!
```

## Index Setup

### Create Index

The vector store automatically creates the index with proper k-NN configuration:

```python
from app.core.vector_store import get_vector_store

# Get vector store instance
vector_store = get_vector_store()

# Create index (idempotent - won't recreate if exists)
vector_store.create_index()
```

### Index Configuration

The index is created with:
- **k-NN enabled** for vector similarity search
- **HNSW algorithm** (Hierarchical Navigable Small World) for efficient nearest neighbor search
- **Cosine similarity** as the distance metric
- **384-dimensional vectors** (default, configurable)

### Index Schema

```json
{
  "settings": {
    "index.knn": true,
    "knn.algo_param.ef_search": 512
  },
  "mappings": {
    "properties": {
      "content": {"type": "text"},
      "embedding": {
        "type": "knn_vector",
        "dimension": 384,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "nmslib"
        }
      },
      "metadata": {"type": "object"},
      "source": {"type": "keyword"},
      "url": {"type": "keyword"},
      "title": {"type": "text"}
    }
  }
}
```

## Usage Examples

### Initialize Vector Store

```python
from app.core.vector_store import get_vector_store

vector_store = get_vector_store()
```

### Add Documents

```python
# Add documents with automatic embedding generation
texts = [
    "How to reset your 401k password",
    "Fidelity brokerage account setup guide",
    "IRA contribution limits for 2024"
]

metadatas = [
    {"source": "fidelity", "url": "https://fidelity.com/help/password"},
    {"source": "fidelity", "url": "https://fidelity.com/help/brokerage"},
    {"source": "mygps", "url": "https://mygps.fmr.com/ira-limits"}
]

doc_ids = vector_store.add_documents(
    texts=texts,
    metadatas=metadatas
)
```

### Vector Similarity Search

```python
# Search for similar documents
results = vector_store.similarity_search(
    query="How do I reset my password?",
    k=5
)

for result in results:
    print(f"Score: {result['score']}")
    print(f"Content: {result['content']}")
    print(f"Source: {result['source']}")
    print(f"URL: {result['url']}")
```

### Hybrid Search (Vector + Keyword)

```python
# Combine semantic and keyword search
results = vector_store.hybrid_search(
    query="401k contribution limits",
    k=5,
    keyword_weight=0.3,  # 30% keyword
    vector_weight=0.7     # 70% semantic
)
```

### Filtered Search

```python
# Search with metadata filters
results = vector_store.similarity_search(
    query="account setup",
    k=5,
    filter_dict={"source": "mygps"}  # Only internal content
)
```

## Index Management

### Check Index Stats

```python
stats = vector_store.get_index_stats()
print(f"Documents: {stats['document_count']}")
print(f"Size: {stats['size_bytes']} bytes")
```

### Recreate Index

```python
# Delete and recreate index (warning: deletes all data!)
vector_store.create_index(force=True)
```

### Delete Index

```python
vector_store.delete_index()
```

## Performance Tuning

### k-NN Parameters

Adjust in `app/core/vector_store.py`:

```python
# Index creation parameters
"knn.algo_param.ef_search": 512,  # Higher = more accurate, slower
"ef_construction": 512,            # Higher = better index quality
"m": 16                            # Number of bi-directional links
```

### Search Parameters

```python
# Retrieve more candidates for better recall
results = vector_store.similarity_search(
    query="...",
    k=10  # Increase top-k
)
```

### Hybrid Search Weights

```python
# Adjust based on use case
results = vector_store.hybrid_search(
    query="...",
    keyword_weight=0.4,   # More weight on exact matches
    vector_weight=0.6     # More weight on semantic similarity
)
```

## Monitoring

### CloudWatch Metrics

Monitor your OpenSearch cluster via AWS CloudWatch:
- **SearchRate**: Requests per second
- **SearchLatency**: Query response time
- **IndexingRate**: Document indexing rate
- **ClusterStatus**: Red/Yellow/Green

### Application Logging

The vector store logs key operations:

```python
# Logs include:
# - Connection establishment
# - Index creation/deletion
# - Document indexing
# - Search queries and results
```

## Troubleshooting

### Connection Issues

**Error**: `ConnectionError: Connection refused`

**Solution**: Check security group and VPC settings. Ensure your application can reach the OpenSearch endpoint.

### Authentication Failures

**Error**: `AuthenticationException`

**Solution**:
1. Verify AWS credentials are correct
2. Check IAM policy allows OpenSearch access
3. If using basic auth, verify username/password

### Index Not Found

**Error**: `index_not_found_exception`

**Solution**:
```python
vector_store.create_index()
```

### Slow Queries

**Symptoms**: High latency on searches

**Solutions**:
1. Increase `ef_search` parameter
2. Add more nodes to OpenSearch cluster
3. Use filters to reduce search space
4. Consider index sharding strategy

### Out of Memory

**Error**: `circuit_breaker_exception`

**Solutions**:
1. Increase OpenSearch instance size
2. Reduce embedding dimension
3. Batch document indexing
4. Enable index refresh interval

## Migration from ChromaDB

If migrating from ChromaDB:

1. **Export ChromaDB documents**:
   ```python
   # From old ChromaDB implementation
   collection = chroma_client.get_collection("faa_knowledge_base")
   documents = collection.get(include=["documents", "metadatas"])
   ```

2. **Import to OpenSearch**:
   ```python
   vector_store = get_vector_store()
   vector_store.create_index()
   vector_store.add_documents(
       texts=documents["documents"],
       metadatas=documents["metadatas"]
   )
   ```

3. **Update configuration**: Remove ChromaDB environment variables, add OpenSearch variables

## Best Practices

1. **Use IAM authentication** in production for better security
2. **Enable SSL/TLS** for encrypted communication
3. **Index in batches** for large datasets (100-500 docs per batch)
4. **Use metadata filters** to narrow search scope
5. **Monitor CloudWatch metrics** for performance issues
6. **Regularly backup** important indices
7. **Use dedicated master nodes** for production clusters
8. **Enable cross-cluster replication** for disaster recovery

## Resources

- [AWS OpenSearch Documentation](https://docs.aws.amazon.com/opensearch-service/)
- [k-NN Plugin Guide](https://opensearch.org/docs/latest/search-plugins/knn/)
- [OpenSearch Python Client](https://opensearch.org/docs/latest/clients/python/)
- [sentence-transformers Documentation](https://www.sbert.net/)

## Support

For issues with OpenSearch configuration:
- AWS Support: Contact your AWS account team
- Internal: #faa-support Slack channel
- GitHub: Create issue in repository
