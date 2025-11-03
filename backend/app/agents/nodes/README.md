# Agent Nodes

This directory contains the individual nodes that make up the LangGraph workflow for the Fidelity Agent Assistant.

## Overview

Each node represents a distinct step in the agent workflow. Nodes are executed in sequence (or parallel where applicable) and pass state between each other via the `AgentState` TypedDict.

## Available Nodes

### 1. Trigger Detection ([trigger_detection.py](trigger_detection.py))

**Purpose**: Detects activation phrases that indicate the agent should start processing.

**Input**:
- `transcript`: Conversation history

**Output**:
- `trigger_detected`: Boolean indicating if workflow should proceed

**Trigger Phrases**:
- "let me take a look"
- "let me check"
- "i'll look into"
- "checking that for you"
- etc.

**Example**:
```python
state = trigger_detection_node(state)
if state["trigger_detected"]:
    # Continue workflow
```

### 2. Query Formulation ([query_formulation.py](query_formulation.py))

**Purpose**: Optimizes the search query from the conversation transcript using LLM.

**Input**:
- `transcript`: Full conversation history
- `feedback_history`: Previous iteration feedback (if retry)

**Output**:
- `optimized_query`: Refined search query
- `query_metadata`: Keywords, entities, intent

**Features**:
- Extracts key financial terms
- Identifies specific products (401k, IRA, etc.)
- Focuses on actionable problems
- Incorporates feedback on retries

**Example**:
```python
state = query_formulation_node(state)
print(state["optimized_query"])  # "401k contribution limits 2024"
print(state["query_metadata"]["intent"])  # "information_request"
```

### 3. Parallel Search ([search.py](search.py))

**Purpose**: Searches multiple sources simultaneously for relevant content.

**Input**:
- `optimized_query`: Search query string

**Output**:
- `search_results`: List of SearchResult objects
- `search_errors`: Any errors encountered

**Search Strategies**:

#### A. Fidelity.com Search
1. **Google Site Search** (Primary)
   - Uses `site:fidelity.com <query>`
   - Most reliable, leverages Google's index
   - Returns top-ranked pages

2. **Fidelity Native Search** (Fallback)
   - Direct search on fidelity.com
   - Parses HTML or JSON responses
   - Used if Google search fails

3. **Content Extraction**
   - Uses `trafilatura` for clean text extraction
   - Falls back to BeautifulSoup if needed
   - Limits content to 2000 chars to avoid token overflow

#### B. myGPS Internal Search
- Requires API credentials
- Searches internal documentation
- Returns structured results

#### C. Vector Store Search (Optional)
- Semantic similarity search in cached content
- Uses OpenSearch k-NN
- Supplements web search results

**Parallel Execution**:
All three sources are searched simultaneously using `asyncio.gather()` for maximum speed.

**Result Format**:
```python
SearchResult = {
    "source": "fidelity" | "mygps" | "vector_store",
    "title": "Page title",
    "url": "https://...",
    "content": "Extracted text content...",
    "relevance_score": 0.0-1.0
}
```

**Example**:
```python
state = await parallel_search_node(state)
print(f"Found {len(state['search_results'])} results")
for result in state["search_results"][:3]:
    print(f"- [{result['source']}] {result['title']}: {result['url']}")
```

### 4. Resolution Generation ([resolution.py](resolution.py))

**Purpose**: Generates customer-ready responses with inline citations using LLM.

**Input**:
- `optimized_query`: Customer's question
- `search_results`: Content from search phase
- `feedback_history`: Feedback from previous iterations

**Output**:
- `resolution_text`: Customer-facing response
- `citations`: Extracted citation metadata
- `generation_timestamp`: When resolution was created

**Features**:
- Synthesizes information from multiple sources
- Includes inline citations: `[Source: URL]`
- Customer-friendly language
- 2-4 paragraph responses
- Step-by-step instructions when applicable

**Citation Format**:
```
According to Fidelity's help documentation [Source: https://fidelity.com/help/...],
you can reset your password by...
```

**Example**:
```python
state = resolution_generation_node(state)
print(state["resolution_text"])
print(f"Citations: {len(state['citations'])}")
```

### 5. Evaluation ([evaluation.py](evaluation.py))

**Purpose**: Evaluates resolution quality using LLM-as-judge and guardrails.

**Input**:
- `optimized_query`: Original question
- `resolution_text`: Generated response
- `search_results`: Sources used

**Output**:
- `evaluation_scores`: Scores on multiple dimensions
- `evaluation_passed`: Boolean indicating if quality threshold met

**Evaluation Criteria** (1-5 scale):

1. **Accuracy**: Does it correctly address the query?
2. **Relevancy**: Is information pertinent to the question?
3. **Factual Grounding**: Are claims supported by sources?
4. **Citation Quality**: Are citations proper and relevant?
5. **Clarity**: Is it clear and well-organized?

**Guardrails**:
- Content safety checks
- Compliance validation
- Citation requirements
- Minimum length requirements

**Quality Gate**:
- Minimum score: 3/5 (configurable via `EVALUATION_MIN_SCORE`)
- All criteria must meet threshold
- Guardrails must pass

**Example**:
```python
state = evaluation_node(state)
if state["evaluation_passed"]:
    print("✓ Quality check passed")
else:
    print(f"✗ Failed: {state['evaluation_scores']['feedback']}")
```

## Workflow Integration

The complete workflow in [workflow.py](../workflow.py) orchestrates these nodes:

```
Trigger Detection → Query Formulation → Parallel Search
                                              ↓
    ┌─────────────────────────────────────────┘
    ↓
Resolution Generation → Evaluation
                           ↓
                    Quality Gate
                     ↙        ↘
              Pass (≥3)    Fail (<3)
                ↓              ↓
           Present      Increment Retry
                              ↓
                      Back to Query Formulation
                      (max 3 retries)
```

## Configuration

Key settings in [config.py](../../config.py):

```python
# Search
SEARCH_TOP_K = 5  # Results per source
SEARCH_TIMEOUT = 10  # Seconds
FIDELITY_SEARCH_URL = "https://www.fidelity.com"
MYGPS_API_URL = "https://mygps.fmr.com/api"
MYGPS_API_KEY = "your_key"

# Evaluation
EVALUATION_MIN_SCORE = 3  # 1-5 scale
EVALUATION_MAX_RETRIES = 3

# LLM
AZURE_OPENAI_API_KEY = "your_key"
AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-4"
AZURE_OPENAI_TEMPERATURE = 0.7
```

## Error Handling

Each node includes comprehensive error handling:

1. **Try-Catch Blocks**: Catch and log all exceptions
2. **Fallback Behavior**: Provide graceful degradation
3. **Error State**: Update `error_message` in state
4. **Logging**: Detailed error logs for debugging

## Testing

### Unit Tests

Test individual nodes in isolation:

```python
# tests/unit/test_nodes.py
import pytest
from app.agents.nodes.search import parallel_search_node
from app.agents.state import create_initial_state

@pytest.mark.asyncio
async def test_parallel_search():
    state = create_initial_state("conv_123", [])
    state["optimized_query"] = "401k contribution limits"

    result = await parallel_search_node(state)

    assert len(result["search_results"]) > 0
    assert result["search_results"][0]["source"] in ["fidelity", "mygps"]
```

### Integration Tests

Test complete workflows:

```python
# tests/integration/test_workflow.py
from app.agents.workflow import run_workflow

@pytest.mark.asyncio
async def test_complete_workflow():
    transcript = [
        {"role": "customer", "content": "How do I reset my password?"},
        {"role": "rep", "content": "Let me check that for you."}
    ]

    result = await run_workflow("conv_123", transcript)

    assert result["status"] == "success"
    assert len(result["resolution"]) > 0
    assert len(result["citations"]) > 0
```

## Performance

### Search Node Performance

- **Google Site Search**: ~1-2 seconds
- **Fidelity Native**: ~2-3 seconds
- **myGPS API**: ~1-2 seconds
- **Vector Store**: ~500ms

**Parallel Execution**: All searches run simultaneously, total time ≈ slowest source (~3 seconds)

### Resolution Generation

- **LLM Call**: ~3-5 seconds (depends on token count)
- **Citation Extraction**: ~50ms

### Evaluation

- **LLM-as-Judge**: ~2-3 seconds
- **Guardrail Checks**: ~100ms

**Total Workflow Time** (first attempt): ~10-15 seconds

## Best Practices

### 1. Query Formulation
- Use low temperature (0.3) for consistency
- Include feedback from previous iterations
- Extract structured metadata for filtering

### 2. Search
- Set reasonable timeouts (10s default)
- Handle HTTP errors gracefully
- Deduplicate results by URL
- Limit content length to avoid token overflow

### 3. Resolution
- Use medium temperature (0.5) for balance
- Always include citations
- Keep responses concise (2-4 paragraphs)
- Use customer-friendly language

### 4. Evaluation
- Use separate LLM instance to avoid bias
- Be strict with scoring (3/5 minimum)
- Provide actionable feedback
- Check guardrails on every response

## Extending the System

### Adding New Search Sources

1. Create new searcher class:
```python
class NewSearcher:
    async def search(self, query: str, k: int) -> List[SearchResult]:
        # Implement search logic
        pass
```

2. Add to `parallel_search_node`:
```python
searcher = NewSearcher()
search_tasks.append(searcher.search(query, k))
```

### Adding New Evaluation Criteria

1. Update `EvaluationOutput` model:
```python
class EvaluationOutput(BaseModel):
    # ... existing fields
    new_criterion: int = Field(description="...", ge=1, le=5)
```

2. Update evaluation prompt with new criterion

3. Update quality gate logic in `evaluation_node`

## Troubleshooting

### Search Returns No Results

**Check**:
1. Network connectivity to fidelity.com
2. Search timeout configuration
3. Query quality (too vague or too specific?)
4. Rate limiting from Google

**Solutions**:
- Increase timeout: `SEARCH_TIMEOUT = 20`
- Improve query formulation prompt
- Add retry logic with exponential backoff

### Resolution Quality Issues

**Check**:
1. Search results quality
2. LLM temperature setting
3. Prompt engineering
4. Token limits

**Solutions**:
- Increase `SEARCH_TOP_K` for more context
- Adjust temperature (0.3-0.7 range)
- Refine resolution prompt
- Increase `AZURE_OPENAI_MAX_TOKENS`

### Evaluation Too Strict/Lenient

**Check**:
1. `EVALUATION_MIN_SCORE` setting
2. Evaluation prompt criteria
3. LLM temperature

**Solutions**:
- Adjust threshold: `EVALUATION_MIN_SCORE = 2` (lenient) or `4` (strict)
- Refine evaluation prompt with examples
- Use lower temperature (0.1) for consistent scoring

## Documentation

- **Main Workflow**: [../workflow.py](../workflow.py)
- **State Definitions**: [../state.py](../state.py)
- **Configuration**: [../../config.py](../../config.py)
- **Architecture**: [../../../../docs/architecture.md](../../../../docs/architecture.md)

## Support

For issues with agent nodes:
- Check logs: `structlog` output in console
- Enable debug logging: `LOG_LEVEL=DEBUG`
- Test nodes individually before integration
- Review Langfuse traces (if configured)
