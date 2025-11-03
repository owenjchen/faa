# Fidelity Agent Assistant (FAA)

An AI-powered chatbot that empowers Fidelity service representatives to better assist customers during live calls and chats. The system listens to conversations, identifies issues, searches internal and public content, generates customer-ready resolutions with citations, and validates responses through an evaluation agent.

## Project Overview

FAA assists service representatives by:
- Processing live customer-rep conversations (voice or text)
- Searching fidelity.com and internal myGPS content
- Generating AI-powered resolutions with citations
- Evaluating response quality with automated metrics
- Providing reps with review/edit capabilities before sending

## Architecture

### Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- LangGraph for agent orchestration
- LangChain for LLM integration
- PostgreSQL + SQLAlchemy
- Redis for caching
- Celery for async tasks
- OpenSearch (AWS) for vector storage

**Frontend:**
- Next.js 14 (App Router)
- React 18 + TypeScript
- shadcn/ui components
- Tailwind CSS
- Socket.IO for real-time updates

**LLM Providers:**
- Azure OpenAI (GPT-4)
- AWS Bedrock (Claude models)

**Observability:**
- Langfuse for LLM tracking
- Prometheus + Grafana for metrics

## Project Structure

```
faa/
├── backend/          # FastAPI backend + agents
├── frontend/         # Next.js frontend
├── docker/           # Docker configurations
├── docs/             # Documentation
└── scripts/          # Utility scripts
```

See [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) for detailed structure.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16+
- Redis 7+
- AWS OpenSearch instance (already configured)
- Azure OpenAI API access (or AWS Bedrock)

### Backend Setup

```bash
cd backend

# Option 1: Using uv (recommended - 10x faster)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Option 2: Using traditional pip
# python -m venv venv
# source venv/bin/activate
# pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your credentials

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

Backend will be available at http://localhost:8000

API docs: http://localhost:8000/api/docs

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.local.example .env.local
# Edit .env.local with API URL

# Start development server
npm run dev
```

Frontend will be available at http://localhost:3000

### Docker Setup (Optional)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Development Workflow

### Backend Development

```bash
# Install development dependencies (if not done already)
uv pip install -e ".[dev]"  # or: pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=app

# Format code
black app/
ruff check app/ --fix

# Type checking
mypy app/
```

### Frontend Development

```bash
# Run tests
npm test

# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format
```

## Key Features

### Phase 1 (MVP)
- [x] Basic text chat interface
- [x] Azure OpenAI integration
- [x] Simple search for fidelity.com
- [x] Resolution generation with citations
- [ ] Manual evaluation

### Phase 2 (Agent System)
- [x] LangGraph workflow
- [x] Automated evaluation agent
- [ ] Feedback loop for retries
- [ ] myGPS integration
- [ ] Langfuse observability

### Phase 3 (Multi-Modal)
- [ ] Voice transcription (Whisper)
- [ ] Multi-LLM support (Bedrock)
- [ ] External guardrails
- [ ] Advanced trigger detection

### Phase 4 (Production)
- [ ] Performance optimization
- [ ] Comprehensive testing
- [ ] Security audit
- [ ] Production deployment

## API Endpoints

### Conversations
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations/{id}` - Get conversation
- `POST /api/v1/conversations/{id}/messages` - Add message
- `POST /api/v1/conversations/{id}/trigger` - Trigger workflow

### Resolutions
- `GET /api/v1/resolutions/{id}` - Get resolution
- `PATCH /api/v1/resolutions/{id}` - Update resolution
- `POST /api/v1/resolutions/{id}/approve` - Approve/reject

### Evaluations
- `GET /api/v1/evaluations/metrics` - Get metrics
- `GET /api/v1/evaluations/scores/{id}` - Get scores

### WebSocket
- `WS /api/v1/ws/conversations/{id}` - Real-time updates

## Configuration

### Backend Environment Variables

See [backend/.env.example](./backend/.env.example) for all configuration options.

Key variables:
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key
- `OPENSEARCH_HOST` - AWS OpenSearch endpoint
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` - AWS credentials for OpenSearch
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `LANGFUSE_PUBLIC_KEY` - Langfuse public key

### Frontend Environment Variables

See [frontend/.env.local.example](./frontend/.env.local.example) for all options.

Key variables:
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_WS_URL` - WebSocket URL

## Testing

### Backend Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/

# With coverage
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
# Unit tests
npm test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

## Deployment

### Docker Production Build

```bash
# Build images
docker-compose -f docker/docker-compose.prod.yml build

# Start services
docker-compose -f docker/docker-compose.prod.yml up -d
```

### Manual Deployment

See [docs/deployment.md](./docs/deployment.md) for detailed instructions.

## Observability

### Langfuse
- Track all LLM calls
- Monitor evaluation metrics
- Analyze token usage
- URL: https://langfuse.fmr.com

### Prometheus + Grafana
- System metrics
- API performance
- Error rates
- Custom dashboards

## Security

- JWT authentication for API
- Rate limiting (60 req/min default)
- CORS protection
- SQL injection prevention (SQLAlchemy ORM)
- Input validation (Pydantic)

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and add tests
3. Run tests and linting
4. Commit: `git commit -m "Description"`
5. Push: `git push origin feature/your-feature`
6. Create Pull Request

## License

Internal Fidelity Investments project.

## Support

For issues or questions:
- Create GitHub issue
- Contact team at team@fidelity.com
- Slack: #faa-support

## Roadmap

**Q4 2024:**
- Complete Phase 1 MVP
- Initial production pilot

**Q1 2025:**
- Phase 2 agent system
- myGPS integration
- Full observability

**Q2 2025:**
- Phase 3 multi-modal
- Voice support
- Multi-LLM

**Q3 2025:**
- Phase 4 production
- Performance optimization
- Full rollout

---

Built with ❤️ by the Fidelity AI Team
