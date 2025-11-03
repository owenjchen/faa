# Getting Started with Fidelity Agent Assistant

This guide will help you get the FAA project up and running quickly.

## What Was Generated

### 1. Complete Project Structure
- **Backend**: FastAPI application with LangGraph agents
- **Frontend**: Next.js 14 with shadcn/ui components
- **Docker**: Development environment configuration
- **Documentation**: Architecture and setup guides

### 2. Core Starter Code

#### Backend Components
- **LangGraph Workflow** ([backend/app/agents/workflow.py](backend/app/agents/workflow.py))
  - Complete agent orchestration with retry logic
  - Quality gate for evaluation scores
  - State management with TypedDict

- **Agent Nodes**:
  - Trigger detection ([backend/app/agents/nodes/trigger_detection.py](backend/app/agents/nodes/trigger_detection.py))
  - Query formulation ([backend/app/agents/nodes/query_formulation.py](backend/app/agents/nodes/query_formulation.py))
  - Search, resolution generation, and evaluation nodes (TODO)

- **FastAPI Endpoints** ([backend/app/api/v1/](backend/app/api/v1/))
  - Conversations API
  - Resolutions API
  - Evaluations API
  - WebSocket for real-time updates

- **Configuration** ([backend/app/config.py](backend/app/config.py))
  - Environment-based settings
  - Azure OpenAI and Bedrock support
  - Database, Redis, and Celery config

#### Frontend Components (Ready for Development)
- Next.js 14 App Router structure
- TypeScript configuration
- Tailwind CSS + shadcn/ui setup
- WebSocket client setup

### 3. Dependencies

#### Backend ([backend/requirements.txt](backend/requirements.txt))
- FastAPI + Uvicorn (web framework)
- LangGraph + LangChain (agent framework)
- Azure OpenAI + Bedrock integrations
- PostgreSQL + SQLAlchemy + Alembic
- Redis + Celery
- ChromaDB + sentence-transformers
- Langfuse observability
- Testing & code quality tools

#### Frontend ([frontend/package.json](frontend/package.json))
- Next.js 14 + React 18 + TypeScript
- Radix UI + shadcn/ui components
- Tailwind CSS + Framer Motion
- Socket.IO client
- Zustand state management
- React Query + SWR
- Testing libraries

## Quick Start (3 Options)

### Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
./scripts/setup.sh

# Follow the on-screen instructions
```

### Option 2: Docker Compose (Easiest)

```bash
# Start all services (Postgres, Redis, Backend, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### Option 3: Manual Setup

#### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure OpenAI and AWS OpenSearch credentials

# Start PostgreSQL and Redis
# macOS: brew services start postgresql redis
# Linux: systemctl start postgresql redis

# Create database
createdb faa_db

# Run migrations (when ready)
# alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000

#### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (optional)
cp .env.local.example .env.local

# Start development server
npm run dev
```

Frontend runs at http://localhost:3000

## Required Configuration

### Backend Environment Variables

Edit `backend/.env` with your credentials:

```bash
# Azure OpenAI (Required)
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# AWS OpenSearch (Required)
OPENSEARCH_HOST=search-faa-xxxxx.us-east-1.es.amazonaws.com
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Database (if not using Docker defaults)
DATABASE_URL=postgresql://faa:faa_password@localhost:5432/faa_db

# Redis (if not using Docker defaults)
REDIS_URL=redis://localhost:6379/0

# Langfuse (Optional - for observability)
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
```

### Frontend Environment Variables

Edit `frontend/.env.local` (optional, has defaults):

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Next Steps

### 1. Complete TODO Items

Several components need implementation:

#### Backend
- [ ] Complete search nodes (fidelity.com scraper)
- [ ] Resolution generation node
- [ ] Evaluation node with scoring logic
- [ ] myGPS integration
- [ ] Database models (SQLAlchemy)
- [ ] Alembic migrations
- [ ] External guardrail integration

#### Frontend
- [ ] Chat UI components
- [ ] Resolution display components
- [ ] WebSocket integration
- [ ] State management setup
- [ ] API client implementation

### 2. Test the Workflow

```python
# Test the LangGraph workflow
cd backend
source venv/bin/activate
python app/agents/workflow.py
```

### 3. Access API Documentation

Visit http://localhost:8000/api/docs to see:
- All API endpoints
- Request/response schemas
- Interactive testing interface

### 4. Explore the Architecture

Key files to understand:
1. [backend/app/agents/workflow.py](backend/app/agents/workflow.py) - Main agent workflow
2. [backend/app/agents/state.py](backend/app/agents/state.py) - State definitions
3. [backend/app/main.py](backend/app/main.py) - FastAPI application
4. [backend/app/config.py](backend/app/config.py) - Configuration management

## Development Workflow

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Backend
black app/              # Format code
ruff check app/ --fix   # Lint
mypy app/               # Type check

# Frontend
npm run format          # Format code
npm run lint            # Lint
npm run type-check      # Type check
```

### Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Architecture Overview

```
┌─────────────┐
│   Rep UI    │  Next.js frontend with real-time updates
└──────┬──────┘
       │ WebSocket + REST
┌──────▼──────┐
│  FastAPI    │  API Gateway & WebSocket server
└──────┬──────┘
       │
┌──────▼──────┐
│  LangGraph  │  Agent orchestration with retry logic
│  Workflow   │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────┐
│  Agent Nodes                             │
│  ┌────────────┐  ┌─────────────────┐   │
│  │ Query      │→ │ Search          │   │
│  │ Formation  │  │ (fidelity+myGPS)│   │
│  └────────────┘  └─────────────────┘   │
│         │               │                │
│  ┌──────▼───────────────▼──────┐        │
│  │ Resolution Generation        │        │
│  └──────────────┬───────────────┘        │
│                 │                         │
│  ┌──────────────▼──────────────┐         │
│  │ Evaluation (Metrics+Guard)  │         │
│  └──────────────┬───────────────┘         │
│                 │                         │
│          Pass ≥ 3? ────NO──→ Retry       │
│                 │                         │
│                YES                        │
└─────────────────┼─────────────────────────┘
                  │
         Present to Rep for Review
```

## Troubleshooting

### Backend won't start
- Check Python version: `python3 --version` (need 3.11+)
- Check virtual environment is activated
- Verify `.env` file exists with Azure OpenAI credentials
- Check PostgreSQL is running: `pg_isready`
- Check Redis is running: `redis-cli ping`

### Frontend won't start
- Check Node version: `node --version` (need 18+)
- Delete `node_modules` and `.next`, then `npm install`
- Check backend is running at http://localhost:8000

### Database errors
- Create database: `createdb faa_db`
- Check connection string in `.env`
- Run migrations: `alembic upgrade head`

### LLM API errors
- Verify Azure OpenAI credentials in `.env`
- Check API endpoint URL format
- Ensure deployment name matches your Azure resource

## Resources

- [Architecture Documentation](./docs/architecture.md)
- [API Documentation](http://localhost:8000/api/docs) (when running)
- [Project Structure](./PROJECT_STRUCTURE.md)
- [CLAUDE.md](./claude.md) - Original requirements

## Support

For issues or questions:
- Check troubleshooting section above
- Review logs: `docker-compose logs -f`
- Check API docs: http://localhost:8000/api/docs

## What's Working vs TODO

### ✅ Working (Generated)
- Complete project structure
- Backend configuration & setup
- LangGraph workflow scaffolding
- FastAPI endpoints (scaffolded)
- Agent state management
- Trigger detection node
- Query formulation node
- All dependencies configured
- Docker environment
- Testing framework setup

### 🚧 TODO (Need Implementation)
- Search integration (fidelity.com, myGPS)
- Resolution generation logic
- Evaluation scoring implementation
- Database models & migrations
- Frontend components
- WebSocket integration
- End-to-end testing
- External guardrail APIs

You now have a solid foundation to build on! Start by implementing the search nodes and resolution generation, then move to the frontend.
