# Fidelity Agent Assistant - Project Structure

```
faa/
├── backend/                              # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                       # FastAPI application entry point
│   │   ├── config.py                     # Configuration management
│   │   ├── dependencies.py               # Dependency injection
│   │   │
│   │   ├── api/                          # API routes
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── conversations.py      # Conversation endpoints
│   │   │   │   ├── resolutions.py        # Resolution endpoints
│   │   │   │   ├── evaluations.py        # Evaluation endpoints
│   │   │   │   └── websocket.py          # WebSocket handlers
│   │   │   └── deps.py                   # Route dependencies
│   │   │
│   │   ├── agents/                       # LangGraph agents
│   │   │   ├── __init__.py
│   │   │   ├── state.py                  # Agent state definitions
│   │   │   ├── workflow.py               # Main LangGraph workflow
│   │   │   ├── nodes/                    # Agent nodes
│   │   │   │   ├── __init__.py
│   │   │   │   ├── trigger_detection.py  # Trigger detection node
│   │   │   │   ├── query_formulation.py  # Query optimization node
│   │   │   │   ├── search.py             # Parallel search node
│   │   │   │   ├── resolution.py         # Resolution generation node
│   │   │   │   └── evaluation.py         # Evaluation node
│   │   │   └── tools/                    # LangChain tools
│   │   │       ├── __init__.py
│   │   │       ├── search_tools.py       # Search tool implementations
│   │   │       └── guardrail_tools.py    # External guardrail tools
│   │   │
│   │   ├── core/                         # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── llm.py                    # LLM client factory
│   │   │   ├── embeddings.py             # Embedding models
│   │   │   ├── vector_store.py           # ChromaDB integration
│   │   │   └── cache.py                  # Redis cache layer
│   │   │
│   │   ├── services/                     # Business services
│   │   │   ├── __init__.py
│   │   │   ├── conversation_service.py   # Conversation management
│   │   │   ├── search_service.py         # Search orchestration
│   │   │   ├── resolution_service.py     # Resolution generation
│   │   │   ├── evaluation_service.py     # Evaluation logic
│   │   │   ├── transcription_service.py  # Whisper integration
│   │   │   └── langfuse_service.py       # Langfuse observability
│   │   │
│   │   ├── models/                       # Database models
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py           # Conversation model
│   │   │   ├── message.py                # Message model
│   │   │   ├── resolution.py             # Resolution model
│   │   │   ├── evaluation.py             # Evaluation model
│   │   │   └── user.py                   # User/Rep model
│   │   │
│   │   ├── schemas/                      # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py           # Conversation DTOs
│   │   │   ├── message.py                # Message DTOs
│   │   │   ├── resolution.py             # Resolution DTOs
│   │   │   ├── evaluation.py             # Evaluation DTOs
│   │   │   └── websocket.py              # WebSocket event schemas
│   │   │
│   │   ├── db/                           # Database management
│   │   │   ├── __init__.py
│   │   │   ├── base.py                   # SQLAlchemy base
│   │   │   ├── session.py                # Database session
│   │   │   └── migrations/               # Alembic migrations
│   │   │       ├── env.py
│   │   │       ├── alembic.ini
│   │   │       └── versions/
│   │   │
│   │   ├── integrations/                 # External integrations
│   │   │   ├── __init__.py
│   │   │   ├── azure_openai.py           # Azure OpenAI client
│   │   │   ├── bedrock.py                # AWS Bedrock client
│   │   │   ├── fidelity_search.py        # fidelity.com scraper
│   │   │   ├── mygps_search.py           # myGPS API client
│   │   │   └── guardrails.py             # External guardrail APIs
│   │   │
│   │   ├── utils/                        # Utilities
│   │   │   ├── __init__.py
│   │   │   ├── logging.py                # Structured logging
│   │   │   ├── metrics.py                # Prometheus metrics
│   │   │   ├── exceptions.py             # Custom exceptions
│   │   │   └── security.py               # Auth & security utils
│   │   │
│   │   └── workers/                      # Celery workers
│   │       ├── __init__.py
│   │       ├── celery_app.py             # Celery configuration
│   │       └── tasks.py                  # Background tasks
│   │
│   ├── tests/                            # Backend tests
│   │   ├── __init__.py
│   │   ├── conftest.py                   # Pytest fixtures
│   │   ├── unit/                         # Unit tests
│   │   │   ├── test_agents.py
│   │   │   ├── test_services.py
│   │   │   └── test_utils.py
│   │   ├── integration/                  # Integration tests
│   │   │   ├── test_api.py
│   │   │   ├── test_workflow.py
│   │   │   └── test_search.py
│   │   └── e2e/                          # End-to-end tests
│   │       └── test_complete_flow.py
│   │
│   ├── requirements.txt                  # Python dependencies
│   ├── requirements-dev.txt              # Development dependencies
│   ├── pyproject.toml                    # Python project config
│   ├── .env.example                      # Environment variables template
│   └── README.md                         # Backend documentation
│
├── frontend/                             # Next.js frontend
│   ├── src/
│   │   ├── app/                          # App Router pages
│   │   │   ├── layout.tsx                # Root layout
│   │   │   ├── page.tsx                  # Home page
│   │   │   ├── dashboard/                # Dashboard pages
│   │   │   │   ├── page.tsx              # Main dashboard
│   │   │   │   └── [conversationId]/     # Conversation detail
│   │   │   │       └── page.tsx
│   │   │   ├── api/                      # API routes (if needed)
│   │   │   │   └── health/
│   │   │   │       └── route.ts
│   │   │   └── globals.css               # Global styles
│   │   │
│   │   ├── components/                   # React components
│   │   │   ├── ui/                       # shadcn/ui components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── textarea.tsx
│   │   │   │   ├── badge.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── toast.tsx
│   │   │   │   └── scroll-area.tsx
│   │   │   │
│   │   │   ├── chat/                     # Chat-specific components
│   │   │   │   ├── ChatContainer.tsx     # Main chat container
│   │   │   │   ├── MessageList.tsx       # Message list display
│   │   │   │   ├── MessageBubble.tsx     # Individual message
│   │   │   │   ├── TranscriptView.tsx    # Live transcript
│   │   │   │   └── InputArea.tsx         # Chat input
│   │   │   │
│   │   │   ├── resolution/               # Resolution components
│   │   │   │   ├── ResolutionCard.tsx    # Resolution display
│   │   │   │   ├── CitationList.tsx      # Citations display
│   │   │   │   ├── EvaluationScores.tsx  # Metrics display
│   │   │   │   ├── EditDialog.tsx        # Edit modal
│   │   │   │   └── ApprovalPanel.tsx     # Approve/Reject panel
│   │   │   │
│   │   │   ├── dashboard/                # Dashboard components
│   │   │   │   ├── ConversationList.tsx  # Active conversations
│   │   │   │   ├── StatsPanel.tsx        # Statistics display
│   │   │   │   └── ActivityFeed.tsx      # Recent activity
│   │   │   │
│   │   │   └── shared/                   # Shared components
│   │   │       ├── Header.tsx            # App header
│   │   │       ├── Sidebar.tsx           # Navigation sidebar
│   │   │       ├── LoadingSpinner.tsx    # Loading indicator
│   │   │       └── ErrorBoundary.tsx     # Error handling
│   │   │
│   │   ├── lib/                          # Utilities & libraries
│   │   │   ├── api.ts                    # API client (axios/fetch)
│   │   │   ├── websocket.ts              # WebSocket client
│   │   │   ├── utils.ts                  # Helper functions
│   │   │   └── cn.ts                     # className utility
│   │   │
│   │   ├── hooks/                        # Custom React hooks
│   │   │   ├── useConversation.ts        # Conversation state
│   │   │   ├── useWebSocket.ts           # WebSocket hook
│   │   │   ├── useResolution.ts          # Resolution actions
│   │   │   └── useAudioRecording.ts      # Audio recording
│   │   │
│   │   ├── store/                        # Zustand stores
│   │   │   ├── conversationStore.ts      # Conversation state
│   │   │   ├── resolutionStore.ts        # Resolution state
│   │   │   └── uiStore.ts                # UI state
│   │   │
│   │   ├── types/                        # TypeScript types
│   │   │   ├── conversation.ts           # Conversation types
│   │   │   ├── message.ts                # Message types
│   │   │   ├── resolution.ts             # Resolution types
│   │   │   ├── evaluation.ts             # Evaluation types
│   │   │   └── websocket.ts              # WebSocket event types
│   │   │
│   │   └── config/                       # Frontend configuration
│   │       ├── constants.ts              # App constants
│   │       └── env.ts                    # Environment variables
│   │
│   ├── public/                           # Static assets
│   │   ├── favicon.ico
│   │   └── images/
│   │
│   ├── tests/                            # Frontend tests
│   │   ├── components/
│   │   ├── hooks/
│   │   └── integration/
│   │
│   ├── package.json                      # Node dependencies
│   ├── tsconfig.json                     # TypeScript config
│   ├── tailwind.config.ts                # Tailwind CSS config
│   ├── next.config.js                    # Next.js config
│   ├── .env.local.example                # Environment variables
│   └── README.md                         # Frontend documentation
│
├── docker/                               # Docker configuration
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   ├── nginx.conf                        # Nginx reverse proxy
│   └── docker-compose.yml                # Local development setup
│
├── docs/                                 # Documentation
│   ├── architecture.md                   # Architecture overview
│   ├── api.md                            # API documentation
│   ├── deployment.md                     # Deployment guide
│   └── development.md                    # Development guide
│
├── scripts/                              # Utility scripts
│   ├── setup.sh                          # Initial setup
│   ├── migrate.sh                        # Database migration
│   └── seed.sh                           # Seed test data
│
├── .github/                              # GitHub configuration
│   ├── workflows/
│   │   ├── backend-tests.yml             # Backend CI
│   │   ├── frontend-tests.yml            # Frontend CI
│   │   └── deploy.yml                    # Deployment workflow
│   └── CODEOWNERS
│
├── .gitignore                            # Git ignore rules
├── README.md                             # Project documentation
├── CLAUDE.md                             # AI assistant instructions
└── LICENSE                               # License file
```

## Directory Descriptions

### Backend (`/backend`)
- **agents/**: LangGraph workflow implementation with state management and node definitions
- **api/**: FastAPI REST endpoints and WebSocket handlers
- **core/**: Core infrastructure (LLM clients, vector stores, caching)
- **services/**: Business logic layer
- **models/**: SQLAlchemy database models
- **schemas/**: Pydantic validation schemas for API
- **integrations/**: External API clients (Azure, Bedrock, search sources)
- **workers/**: Celery background tasks

### Frontend (`/frontend`)
- **app/**: Next.js 14 App Router pages and layouts
- **components/**: React components organized by feature
- **lib/**: Utility functions and API clients
- **hooks/**: Custom React hooks for state and side effects
- **store/**: Zustand state management stores
- **types/**: TypeScript type definitions

### Infrastructure
- **docker/**: Containerization configs for all services
- **docs/**: Technical documentation
- **scripts/**: DevOps and utility scripts
