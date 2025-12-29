"""
ShariahFolio LangGraph Agent Module
A tool-based conversational agent that uses LangChain tools for portfolio optimization.

This agent uses a ReAct pattern where the LLM decides when to call tools
to get real data, ensuring no hallucinated portfolio results.
"""

import logging
from typing import TypedDict, Annotated, List, Optional, Sequence
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    BaseMessage,
    ToolMessage
)

from .config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
)
from .tools import get_portfolio_tools
from .utils.prompt_loader import load_prompt

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_MESSAGE_HISTORY = 30  # Maximum messages to keep in history


# =============================================================================
# AGENT STATE
# =============================================================================

class AgentState(TypedDict):
    """State for the portfolio agent."""
    messages: Annotated[List[BaseMessage], "Conversation history"]
    pending_tool_calls: Optional[List[dict]]
    tool_call_count: int  # Counter to prevent infinite tool calling loops


# Maximum number of tool calls allowed per user message
MAX_TOOL_CALLS_PER_REQUEST = 3


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def trim_message_history(
    messages: List[BaseMessage],
    max_messages: int = MAX_MESSAGE_HISTORY
) -> List[BaseMessage]:
    """
    Trim message history to prevent token overflow.
    Keeps the most recent messages.
    """
    if len(messages) <= max_messages:
        return messages
    return messages[-max_messages:]


def get_system_prompt() -> str:
    """Get the system prompt for the agent."""
    try:
        return load_prompt("consultant_system")
    except FileNotFoundError:
        logger.warning("System prompt file not found, using fallback")
        return _get_fallback_system_prompt()


def _get_fallback_system_prompt() -> str:
    """Fallback system prompt if file loading fails."""
    return """You are ShariahFolio, an AI investment advisor for Shariah-compliant Egyptian stocks (EGX 33 Index).

IMPORTANT RULES:
1. ALWAYS use the `optimize_portfolio` tool to generate portfolios - NEVER make up numbers
2. ALWAYS use `get_stock_info` for stock details
3. Gather investment amount and either specific tickers or risk profile before optimizing

Available tools:
- optimize_portfolio: Create optimized portfolio (needs: investment_amount, and either tickers or risk_profile)
- get_stock_info: Get stock details (needs: ticker)
- list_available_stocks: Show all available stocks
- get_stocks_by_risk_profile: Preview stocks for a risk level

Be helpful, concise, and professional."""


def create_llm():
    """Create the LLM client with tools bound."""
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set. LLM calls will fail.")

    tools = get_portfolio_tools()

    llm = ChatOpenAI(
        model=OPENROUTER_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        temperature=0.7,
        max_tokens=2048
    )

    # Bind tools to the LLM
    return llm.bind_tools(tools)


# =============================================================================
# GRAPH NODES
# =============================================================================

def agent_node(state: AgentState) -> AgentState:
    """
    The main agent node that processes messages and decides on actions.
    Uses the LLM to either respond directly or call tools.
    """
    tool_call_count = state.get("tool_call_count", 0)
    logger.info(f"Agent node - Processing messages (tool_call_count: {tool_call_count})")

    # Check if we've exceeded the tool call limit
    if tool_call_count >= MAX_TOOL_CALLS_PER_REQUEST:
        logger.warning(f"Tool call limit ({MAX_TOOL_CALLS_PER_REQUEST}) reached, forcing response")

        # Check if the last tool result was an error
        last_tool_result = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage):
                last_tool_result = msg.content
                break

        # Generate appropriate forced response based on tool results
        if last_tool_result and "Error" in last_tool_result:
            forced_content = f"I encountered an issue while processing your request. {last_tool_result}\n\nCould you please try rephrasing your request or provide different parameters?"
        elif last_tool_result and "## Portfolio" in last_tool_result:
            # Tool succeeded, present the results
            forced_content = f"Here are your portfolio optimization results:\n\n{last_tool_result}"
        else:
            forced_content = "I've gathered the portfolio information. Based on my analysis, please see the results above. Let me know if you'd like any adjustments or have questions about the allocation!"

        forced_response = AIMessage(content=forced_content)
        return {
            "messages": list(state["messages"]) + [forced_response],
            "pending_tool_calls": None,
            "tool_call_count": tool_call_count
        }

    llm = create_llm()

    # Build messages with system prompt
    system_prompt = get_system_prompt()
    messages = [SystemMessage(content=system_prompt)]

    # Add conversation history (trimmed)
    trimmed_history = trim_message_history(state["messages"])
    messages.extend(trimmed_history)

    # Invoke LLM
    try:
        response = llm.invoke(messages)
        logger.info(f"LLM response type: {type(response).__name__}, has tool_calls: {bool(response.tool_calls)}")
    except Exception as e:
        logger.exception(f"LLM invocation failed: {e}")
        error_message = AIMessage(
            content="I'm having trouble connecting to my AI service. Please try again in a moment."
        )
        return {
            "messages": list(state["messages"]) + [error_message],
            "pending_tool_calls": None,
            "tool_call_count": tool_call_count
        }

    # Add response to messages
    new_messages = list(state["messages"]) + [response]

    # Check if there are tool calls
    if response.tool_calls:
        logger.info(f"Tool calls requested: {[tc['name'] for tc in response.tool_calls]}")
        for tc in response.tool_calls:
            logger.info(f"  Tool: {tc['name']}")
            logger.info(f"  Args: {tc.get('args', {})}")
        return {
            "messages": new_messages,
            "pending_tool_calls": response.tool_calls,
            "tool_call_count": tool_call_count  # Will be incremented in tool_executor_node
        }
    else:
        logger.info("No tool calls, returning response directly")
        return {
            "messages": new_messages,
            "pending_tool_calls": None,
            "tool_call_count": tool_call_count
        }


def tool_executor_node(state: AgentState) -> AgentState:
    """
    Execute tool calls and return results.
    """
    tool_call_count = state.get("tool_call_count", 0)
    logger.info(f"Tool executor node - Executing tools (count: {tool_call_count})")

    tools = get_portfolio_tools()
    tool_node = ToolNode(tools)

    # Get the last message (which should have tool calls)
    last_message = state["messages"][-1]

    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        logger.warning("No tool calls found in last message")
        return state

    # Increment tool call counter
    tool_call_count += 1
    logger.info(f"Tool call count incremented to: {tool_call_count}")

    # Log the tool calls being executed
    for tc in last_message.tool_calls:
        logger.info(f"Executing tool: {tc['name']} with args: {tc.get('args', {})}")

    # Execute tools
    try:
        # ToolNode expects the state with messages
        result = tool_node.invoke(state)

        # Result contains new messages with tool outputs
        new_messages = list(state["messages"])

        # Add tool result messages
        if "messages" in result:
            for msg in result["messages"]:
                new_messages.append(msg)
                logger.info(f"Tool result added: {type(msg).__name__}")
                # Log the first 500 chars of the tool result
                content_preview = str(msg.content)[:500] if hasattr(msg, 'content') else 'N/A'
                logger.info(f"Tool result preview: {content_preview}")

        return {
            "messages": new_messages,
            "pending_tool_calls": None,
            "tool_call_count": tool_call_count
        }

    except Exception as e:
        logger.exception(f"Tool execution failed: {e}")
        # Add error as tool message
        error_msg = ToolMessage(
            content=f"Error executing tool: {str(e)}",
            tool_call_id=last_message.tool_calls[0]["id"] if last_message.tool_calls else "error"
        )
        return {
            "messages": list(state["messages"]) + [error_msg],
            "pending_tool_calls": None,
            "tool_call_count": tool_call_count
        }


def should_continue(state: AgentState) -> str:
    """
    Determine the next node based on whether there are pending tool calls.
    """
    last_message = state["messages"][-1] if state["messages"] else None

    # If the last message is from a tool, go back to agent
    if isinstance(last_message, ToolMessage):
        logger.info("Routing: tool_result -> agent")
        return "agent"

    # If there are tool calls, execute them
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        logger.info("Routing: has_tool_calls -> tools")
        return "tools"

    # Otherwise, we're done
    logger.info("Routing: no_tool_calls -> end")
    return "end"


# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================

def create_agent_graph():
    """Create and return the LangGraph agent with tools."""

    # Build the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_executor_node)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )

    # After tools, always go back to agent
    workflow.add_edge("tools", "agent")

    return workflow.compile()


# =============================================================================
# PORTFOLIO AGENT CLASS
# =============================================================================

class PortfolioAgent:
    """High-level agent interface for the web application."""

    def __init__(self):
        self.graph = create_agent_graph()
        self._init_state()
        logger.info("PortfolioAgent initialized with tool-based architecture")

    def _init_state(self) -> None:
        """Initialize or reset the agent state."""
        self.state: AgentState = {
            "messages": [],
            "pending_tool_calls": None,
            "tool_call_count": 0
        }

    def reset(self) -> None:
        """Reset the conversation state."""
        logger.info("Resetting agent state")
        self._init_state()

    async def chat(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.
        """
        logger.info(f"Processing user message: {user_message[:100]}...")

        # Add user message to state and reset tool call counter for new message
        self.state["messages"] = list(self.state["messages"])
        self.state["messages"].append(HumanMessage(content=user_message))
        self.state["tool_call_count"] = 0  # Reset counter for each new user message

        # Run the graph with recursion limit to prevent runaway loops
        try:
            result = self.graph.invoke(
                self.state,
                config={"recursion_limit": 10}  # Limit to 10 iterations max
            )

            # Update state
            self.state = result

            # Trim message history
            self.state["messages"] = trim_message_history(self.state["messages"])

        except Exception as e:
            logger.exception(f"Graph invocation failed: {e}")
            error_response = "I encountered an error processing your request. Please try again."
            self.state["messages"].append(AIMessage(content=error_response))
            return error_response

        # Return the last AI message content
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                # Skip messages that are just tool calls without content
                if msg.content.strip():
                    return msg.content

        return "I'm processing your request..."

    def get_last_response(self) -> str:
        """Get the last AI response."""
        for msg in reversed(self.state["messages"]):
            if isinstance(msg, AIMessage) and msg.content and msg.content.strip():
                return msg.content
        return ""

    def get_message_count(self) -> int:
        """Get the number of messages in the conversation."""
        return len(self.state["messages"])
