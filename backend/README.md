# FAA Backend

Fidelity Agent Assistant backend API built with FastAPI and LangGraph.

## Quick Start

### Using UV (Recommended - 10x Faster)

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
#uv pip install -r requirements.txt
uv pip install -r pyproject.toml

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Run server
uvicorn app.main:app --reload
```

### Using pip (Traditional)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials

uvicorn app.main:app --reload
```

## Development

### Install Dev Dependencies

```bash
# With uv
uv pip install -e ".[dev]"

# With pip
pip install -r requirements-dev.txt
```

### Common Commands

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Format code
black app/

# Lint code
ruff check app/ --fix

# Type check
mypy app/

# Run server
uvicorn app.main:app --reload

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Configuration

### Required Environment Variables

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# AWS OpenSearch
OPENSEARCH_HOST=search-faa-xxxxx.us-east-1.es.amazonaws.com
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/faa_db

# Redis
REDIS_URL=redis://localhost:6379/0
```

See [.env.example](.env.example) for all configuration options.

## Project Structure

```
backend/
├── app/
│   ├── agents/          # LangGraph agents and workflows
│   ├── api/             # FastAPI routes
│   ├── core/            # Core infrastructure (vector store, etc.)
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── utils/           # Utilities
├── tests/               # Test suite
├── requirements.txt     # Production dependencies
├── requirements-dev.txt # Development dependencies
└── pyproject.toml       # Project configuration
```

## API Documentation

When running locally, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Architecture

- **Framework**: FastAPI
- **Agent Orchestration**: LangGraph
- **LLM Integration**: LangChain (Azure OpenAI + AWS Bedrock)
- **Vector Store**: AWS OpenSearch
- **Database**: PostgreSQL + SQLAlchemy
- **Cache**: Redis
- **Task Queue**: Celery
- **Observability**: Langfuse + Prometheus

## Key Features

- **Real-time conversation processing** via WebSocket
- **Agent-based workflow** with retry logic and quality gates
- **Vector similarity search** with OpenSearch k-NN
- **Hybrid search** (semantic + keyword)
- **LLM evaluation** with automated scoring
- **Citation tracking** for all generated content

## Documentation

- **Main README**: [../README.md](../README.md)
- **Getting Started**: [../GETTING_STARTED.md](../GETTING_STARTED.md)
- **OpenSearch Setup**: [../docs/OPENSEARCH_SETUP.md](../docs/OPENSEARCH_SETUP.md)
- **UV Setup**: [../docs/UV_SETUP.md](../docs/UV_SETUP.md)
- **Project Structure**: [../PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)

## Troubleshooting

### Import Errors

```bash
# Ensure dependencies are installed
uv pip install -r requirements.txt

# Reinstall in editable mode
uv pip install -e .
```

### Database Connection

```bash
# Check PostgreSQL is running
pg_isready

# Create database
createdb faa_db

# Run migrations
alembic upgrade head
```

### OpenSearch Connection

```bash
# Test connection
python -c "from app.core.vector_store import get_vector_store; vs = get_vector_store(); print('Connected!')"
```

### Redis Connection

```bash
# Check Redis is running
redis-cli ping
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_agents.py

# Run with coverage
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Performance

Using **uv** for package management provides significant speedups:

| Operation | pip | uv | Speedup |
|-----------|-----|-----|---------|
| Cold install | ~120s | ~8s | 15x |
| Warm install | ~45s | ~2s | 22x |
| Dependency resolution | ~30s | ~1s | 30x |

## Support

- **Documentation**: See docs/ directory
- **Issues**: Create GitHub issue
- **Slack**: #faa-support

## License

Internal Fidelity Investments project.
