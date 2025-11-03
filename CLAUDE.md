# Fidelity Agent Assistant (FAA)

## Project Overview
An AI-powered chatbot that empowers Fidelity service representatives to better assist customers during live calls and chats. The system listens to conversations, identifies issues, searches internal and public content, generates customer-ready resolutions with citations, and validates responses through an evaluation agent before presenting them to reps.

## Core Objectives
1. **Real-time Assistance**: Process live customer-rep conversations (voice or text)
2. **Intelligent Search**: Query fidelity.com and myGPS (internal content) with optimized search queries
3. **Quality Assurance**: Evaluate AI-generated responses using LLM-based evaluation and external guardrails
4. **Rep Control**: Representatives review, edit, and approve all responses before sending to customers

## Technical Requirements

### LLM Support
- **Azure OpenAI**: GPT-4.1, GPT-5 and other OpenAI models
- **Amazon Bedrock**: Claude models (Sonnet, Opus)
- **Local Models**: Support for self-hosted LLM endpoints

### Key Integrations
- **Langfuse** (langfuse.fmr.com): Observability and evaluation tracking
- **Content Sources**: 
  - fidelity.com (public search)
  - myGPS.com (internal content search)
- **External Guardrails**: API-based validation services

### Technology Stack Constraints
- Use **open-source tools only** (except LLM API calls)
- Modern web UI (similar to Claude/ChatGPT UX)
- Agent framework for task orchestration
- Support both text chat and voice interfaces

## System Architecture

### Components
1. **Conversation Monitor**: Listens to live calls/chats, transcribes audio if needed
2. **Trigger Detection**: Identifies activation phrases (e.g., "let me take a look")
3. **Agent Orchestrator**: Manages the agentic workflow
4. **Search Module**: Parallel searches across multiple sources
5. **Resolution Generator**: Creates initial customer-ready responses
6. **Evaluation Agent**: Validates responses using metrics and guardrails
7. **Rep Interface**: UI for review, editing, and approval

### Workflow Pipeline
```
Customer Issue → Rep Clarification → Trigger Phrase Detected
                                            ↓
                                    FAA Activation
                                            ↓
┌───────────────────────────────────────────────────────────────┐
│ 1. Query Formulation: Optimize search query from transcript   │
├───────────────────────────────────────────────────────────────┤
│ 2. Parallel Search: fidelity.com + myGPS.com (top-k results) │
├───────────────────────────────────────────────────────────────┤
│ 3. Resolution Generation: LLM creates response + citations    │
├───────────────────────────────────────────────────────────────┤
│ 4. Evaluation: Metrics (1-5 scale)                           │
│    - Accuracy                                                  │
│    - Relevancy                                                 │
│    - Factual Grounding                                         │
│    - External guardrail checks                                 │
├───────────────────────────────────────────────────────────────┤
│ 5. Quality Gate: All metrics ≥ 3?                            │
│    NO  → Return to step 1 (with history)                      │
│    YES → Present to rep                                        │
└───────────────────────────────────────────────────────────────┘
                        ↓
        Rep Reviews → Approve/Edit/Reject
                        ↓
        (If edited/rejected → Return to step 1)
```

## Development Priorities

### Phase 1: MVP (Core Functionality)
- [ ] Basic text chat interface
- [ ] Single LLM integration (recommend starting with Azure OpenAI)
- [ ] Simple search implementation for fidelity.com
- [ ] Basic resolution generation with citations
- [ ] Manual evaluation (no automated agent yet)

### Phase 2: Agent System
- [ ] Implement agent framework (LangGraph recommended)
- [ ] Add evaluation agent with metrics scoring
- [ ] Implement feedback loop for sub-threshold scores
- [ ] Add myGPS.com search integration
- [ ] Langfuse integration for observability

### Phase 3: Multi-Modal & Advanced Features
- [ ] Voice interface and transcription
- [ ] Support for multiple LLM providers (Bedrock, local models)
- [ ] External guardrail API integrations
- [ ] Advanced trigger detection
- [ ] Conversation history and context management

### Phase 4: Production Readiness
- [ ] Rep UI/UX refinement
- [ ] Performance optimization (caching, parallel processing)
- [ ] Comprehensive testing suite
- [ ] Security and compliance reviews
- [ ] Deployment infrastructure

## Key Implementation Notes

### Agent Framework Selection
Consider these options:
- **LangGraph**: Best for complex workflows with human-in-the-loop
- **OpenAI Agent SDK**: Native OpenAI Agent SDK

### Search Strategy
- Implement semantic search for better relevance
- Use embedding models to match queries with content
- Return top-k results (recommend k=5-10 per source)
- Include metadata (source URL, confidence score, timestamp)

### Evaluation Metrics
- **Accuracy**: Does the resolution correctly address the issue?
- **Relevancy**: Is the information pertinent to the customer's question?
- **Factual Grounding**: Are all claims supported by cited sources?
- Threshold: All metrics must score ≥ 3 (on 1-5 scale)

### Citation Format
- Include source URLs with each claim
- Use inline citations like: "According to [Source Name](URL), ..."
- Ensure traceability for compliance

### Error Handling
- Maximum retry attempts for low-quality responses (recommend 3)
- Escalation path if automated resolution fails
- Fallback options for search/LLM failures

## Testing Strategy
- Unit tests for each component
- Integration tests for workflow pipeline
- End-to-end tests simulating customer scenarios
- Evaluation quality tests (validate metric scoring)
- Load testing for concurrent rep sessions

## Security & Compliance Considerations
- Data privacy for customer conversations
- Access controls for internal content (myGPS)
- Audit logging for all AI-generated responses
- Compliance with financial services regulations

## Getting Started
1. Set up development environment with Python 3.10+
2. Configure LLM API credentials (Azure OpenAI)
3. Implement basic chat interface
4. Build search integration for fidelity.com
5. Create simple resolution generator
6. Iterate and expand based on feedback

---

**Note**: Representatives maintain full control over all customer communications. FAA is an assistant tool, not an autonomous agent.