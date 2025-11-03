# OpenSearch Migration Summary

This document summarizes the changes made to replace ChromaDB with AWS OpenSearch as the vector store.

## Changes Made

### 1. Backend Configuration ([backend/app/config.py](backend/app/config.py:55))

**Removed:**
```python
# Vector Store - ChromaDB
CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
CHROMA_COLLECTION_NAME: str = "faa_knowledge_base"
```

**Added:**
```python
# Vector Store - OpenSearch (AWS)
OPENSEARCH_HOST: Optional[str] = None
OPENSEARCH_PORT: int = 443
OPENSEARCH_USERNAME: Optional[str] = None
OPENSEARCH_PASSWORD: Optional[str] = None
OPENSEARCH_USE_SSL: bool = True
OPENSEARCH_VERIFY_CERTS: bool = True
OPENSEARCH_INDEX_NAME: str = "faa_knowledge_base"
OPENSEARCH_VECTOR_FIELD: str = "embedding"
OPENSEARCH_TEXT_FIELD: str = "content"
OPENSEARCH_METADATA_FIELD: str = "metadata"
```

### 2. Dependencies ([backend/requirements.txt](backend/requirements.txt:32))

**Removed:**
```
chromadb==0.4.24
```

**Added:**
```
opensearch-py==2.7.1
requests-aws4auth==1.3.1
```

### 3. Vector Store Implementation ([backend/app/core/vector_store.py](backend/app/core/vector_store.py:1))

**Created new file** with `OpenSearchVectorStore` class featuring:

- **IAM Authentication**: Automatic AWS IAM auth when username/password not provided
- **Basic Authentication**: Support for username/password if configured
- **k-NN Vector Search**: Optimized HNSW algorithm for fast similarity search
- **Hybrid Search**: Combination of vector similarity and keyword search
- **Index Management**: Create, delete, and manage indices
- **Metadata Filtering**: Filter search results by metadata fields

#### Key Methods:

```python
# Initialize
vector_store = OpenSearchVectorStore()

# Create index with k-NN configuration
vector_store.create_index()

# Add documents (automatic embedding generation)
vector_store.add_documents(texts, metadatas, ids)

# Vector similarity search
results = vector_store.similarity_search(query, k=5)

# Hybrid search (vector + keyword)
results = vector_store.hybrid_search(query, k=5, keyword_weight=0.3)

# Get statistics
stats = vector_store.get_index_stats()
```

### 4. Environment Configuration ([backend/.env.example](backend/.env.example:38))

**Updated** with OpenSearch configuration:

```bash
# OpenSearch Vector Store Configuration (AWS)
OPENSEARCH_HOST=search-faa-xxxxx.us-east-1.es.amazonaws.com
OPENSEARCH_PORT=443
OPENSEARCH_USERNAME=
OPENSEARCH_PASSWORD=
OPENSEARCH_USE_SSL=true
OPENSEARCH_VERIFY_CERTS=true
OPENSEARCH_INDEX_NAME=faa_knowledge_base
OPENSEARCH_VECTOR_FIELD=embedding
OPENSEARCH_TEXT_FIELD=content
OPENSEARCH_METADATA_FIELD=metadata
```

### 5. Documentation Updates

#### [README.md](README.md:25)
- Changed "ChromaDB for vector storage" → "OpenSearch (AWS) for vector storage"
- Added AWS OpenSearch instance to prerequisites
- Added OpenSearch configuration to key variables

#### [GETTING_STARTED.md](GETTING_STARTED.md:106)
- Updated setup instructions to mention OpenSearch credentials
- Added OpenSearch environment variables to configuration section

#### [docs/OPENSEARCH_SETUP.md](docs/OPENSEARCH_SETUP.md:1) (New)
- Complete OpenSearch setup guide
- Authentication configuration (IAM and Basic Auth)
- Usage examples and code snippets
- Performance tuning guidelines
- Troubleshooting section
- Migration guide from ChromaDB

### 6. Docker & Scripts

#### [docker/backend.Dockerfile](docker/backend.Dockerfile:21)
- Removed `RUN mkdir -p data/chroma` (no longer needed)

#### [scripts/setup.sh](scripts/setup.sh:80)
- Removed ChromaDB data directory creation

#### [.gitignore](.gitignore:80)
- Removed `data/chroma/` entry

## OpenSearch Architecture

### Index Structure

```json
{
  "settings": {
    "index.knn": true,
    "knn.algo_param.ef_search": 512,
    "number_of_shards": 2,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "content": {
        "type": "text",
        "analyzer": "standard"
      },
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

### Search Flow

```
User Query
    ↓
sentence-transformers
(Generate embedding)
    ↓
OpenSearch k-NN Search
    ↓
HNSW Algorithm
(Cosine similarity)
    ↓
Top-K Results
    ↓
Score + Content + Metadata
```

## Configuration Required

### Minimum Configuration

```bash
# Required
OPENSEARCH_HOST=your-opensearch-endpoint.us-east-1.es.amazonaws.com
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
```

### Full Configuration (Optional)

```bash
# OpenSearch Connection
OPENSEARCH_HOST=your-opensearch-endpoint.us-east-1.es.amazonaws.com
OPENSEARCH_PORT=443
OPENSEARCH_USE_SSL=true
OPENSEARCH_VERIFY_CERTS=true

# Authentication (choose one)
# Option 1: IAM (leave username/password empty)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Option 2: Basic Auth
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=your_password

# Index Configuration
OPENSEARCH_INDEX_NAME=faa_knowledge_base
OPENSEARCH_VECTOR_FIELD=embedding
OPENSEARCH_TEXT_FIELD=content
OPENSEARCH_METADATA_FIELD=metadata

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

## Usage in Application

### Importing

```python
from app.core.vector_store import get_vector_store

# Get global instance
vector_store = get_vector_store()
```

### In Agent Workflow

```python
from app.agents.nodes.search import parallel_search_node

# The search node will use OpenSearch automatically
def parallel_search_node(state: AgentState) -> AgentState:
    vector_store = get_vector_store()

    # Semantic search for relevant content
    results = vector_store.similarity_search(
        query=state["optimized_query"],
        k=settings.SEARCH_TOP_K
    )

    state["search_results"] = results
    return state
```

## Benefits Over ChromaDB

### Performance
- **Scalability**: Distributed architecture handles millions of documents
- **Speed**: HNSW algorithm provides sub-linear search time
- **Concurrent Access**: Multiple workers can query simultaneously

### Features
- **Hybrid Search**: Combine vector and keyword search
- **Filtering**: Metadata-based filtering at query time
- **Index Management**: Professional tools for monitoring and optimization

### Infrastructure
- **Managed Service**: AWS handles scaling, backups, updates
- **High Availability**: Multi-AZ deployment with automatic failover
- **Security**: IAM integration, VPC isolation, encryption at rest/transit

### Enterprise
- **Monitoring**: CloudWatch metrics and alarms
- **Compliance**: SOC, HIPAA, PCI-DSS certified
- **Support**: AWS enterprise support available

## Testing

### Verify Installation

```python
# Test OpenSearch connection
from app.core.vector_store import get_vector_store

vector_store = get_vector_store()
print("OpenSearch connected successfully!")

# Create index
vector_store.create_index()
print("Index created!")

# Add test document
vector_store.add_documents(
    texts=["Test document"],
    metadatas=[{"source": "test"}]
)
print("Document indexed!")

# Search
results = vector_store.similarity_search("test", k=1)
print(f"Found {len(results)} results")
```

### Run Tests

```bash
cd backend
pytest tests/ -v -k opensearch
```

## Migration Checklist

- [x] Update `backend/app/config.py` with OpenSearch settings
- [x] Update `backend/requirements.txt` to use `opensearch-py`
- [x] Create `backend/app/core/vector_store.py` with OpenSearch integration
- [x] Update `backend/.env.example` with OpenSearch configuration
- [x] Update README.md documentation
- [x] Update GETTING_STARTED.md guide
- [x] Create `docs/OPENSEARCH_SETUP.md` detailed guide
- [x] Remove ChromaDB references from Docker files
- [x] Remove ChromaDB data directory from setup scripts
- [x] Update .gitignore

## Next Steps

1. **Configure AWS OpenSearch**:
   - Ensure OpenSearch instance is running
   - Get the endpoint URL
   - Configure IAM permissions or basic auth

2. **Update Environment Variables**:
   ```bash
   cp backend/.env.example backend/.env
   # Edit .env with your OpenSearch endpoint and AWS credentials
   ```

3. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Initialize Index**:
   ```python
   from app.core.vector_store import get_vector_store

   vector_store = get_vector_store()
   vector_store.create_index()
   ```

5. **Test Integration**:
   ```bash
   python -c "from app.core.vector_store import get_vector_store; vs = get_vector_store(); print('Connected!')"
   ```

## Support

- **OpenSearch Setup**: See [docs/OPENSEARCH_SETUP.md](docs/OPENSEARCH_SETUP.md:1)
- **AWS Configuration**: Contact AWS administrator
- **Code Issues**: Create GitHub issue
- **Questions**: #faa-support Slack channel

---

**Migration completed successfully!** The application now uses AWS OpenSearch for all vector storage operations.
