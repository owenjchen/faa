"""Query formulation node - optimizes search queries from conversation transcript."""

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class QueryOptimization(BaseModel):
    """Structured output for query optimization."""
    optimized_query: str = Field(description="Optimized search query for content retrieval")
    keywords: list[str] = Field(description="Key terms extracted from conversation")
    entities: list[str] = Field(description="Named entities (accounts, products, issues)")
    intent: str = Field(description="Customer's primary intent or problem")
    context: str = Field(description="Additional context for search personalization")


QUERY_FORMULATION_PROMPT = """You are a search query optimization specialist for Fidelity financial services.

Your task is to analyze a conversation transcript between a customer and service representative,
then generate an optimized search query to find relevant help content.

## Conversation Transcript:
{transcript}

## Previous Feedback (if retry):
{feedback}

## Instructions:
1. Identify the customer's core issue or question
2. Extract key financial terms, account types, and specific problems
3. Create a concise search query (5-10 words) optimized for semantic search
4. List important keywords and entities
5. Determine the customer's primary intent

## Guidelines:
- Focus on actionable problems, not general conversation
- Include specific product names (401k, IRA, brokerage, etc.)
- Prioritize technical terms over conversational language
- If this is a retry, incorporate the feedback to improve the query

Return your analysis in JSON format.
"""


def query_formulation_node(state: AgentState) -> AgentState:
    """
    Formulate optimized search query from conversation transcript.

    Args:
        state: Current agent state with transcript

    Returns:
        Updated state with optimized_query and query_metadata
    """
    logger.info(f"Formulating query for conversation {state['conversation_id']}")

    try:
        # Initialize LLM
        llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            deployment_name=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            temperature=0.3,  # Lower temperature for consistent query generation
        )

        # Create prompt
        prompt = ChatPromptTemplate.from_template(QUERY_FORMULATION_PROMPT)

        # Format transcript
        transcript_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in state["transcript"]
        ])

        # Get previous feedback if this is a retry
        feedback = "\n".join(state["feedback_history"]) if state["feedback_history"] else "None"

        # Create chain with structured output
        parser = JsonOutputParser(pydantic_object=QueryOptimization)
        chain = prompt | llm | parser

        # Execute
        result = chain.invoke({
            "transcript": transcript_text,
            "feedback": feedback
        })

        # Update state
        state["optimized_query"] = result["optimized_query"]
        state["query_metadata"] = {
            "keywords": result["keywords"],
            "entities": result["entities"],
            "intent": result["intent"],
            "context": result["context"]
        }

        logger.info(
            f"Query formulated: '{result['optimized_query']}' "
            f"(intent: {result['intent']})"
        )

        return state

    except Exception as e:
        logger.exception(f"Query formulation failed: {str(e)}")
        state["error_message"] = f"Query formulation error: {str(e)}"
        # Fallback: use last customer message as query
        customer_messages = [
            msg["content"] for msg in state["transcript"]
            if msg["role"] == "customer"
        ]
        if customer_messages:
            state["optimized_query"] = customer_messages[-1][:100]
        return state
