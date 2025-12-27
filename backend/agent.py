"""
ShariahFolio LangGraph Agent Module
A conversational agent that gathers user constraints and triggers portfolio optimization.
"""

import json
import re
from typing import TypedDict, Annotated, List, Optional, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from .config import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL,
    EGX33_TICKERS, RISK_PROFILES, TICKER_NAMES
)
from .portfolio_model import get_optimizer
from .data_loader import get_data_loader


# Agent State
class AgentState(TypedDict):
    """State for the portfolio agent."""
    messages: Annotated[List[BaseMessage], "Conversation history"]
    investment_amount: Optional[float]
    preferred_stocks: List[str]
    risk_profile: Optional[str]
    allocation: Optional[dict]
    error: Optional[str]
    current_node: str
    needs_info: bool


def create_llm():
    """Create the LLM client for OpenRouter."""
    return ChatOpenAI(
        model=OPENROUTER_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        temperature=0.7,
        max_tokens=1024
    )


# System prompt for the consultant
CONSULTANT_SYSTEM_PROMPT = """You are ShariahFolio, an expert Islamic finance advisor specializing in the Egyptian Exchange (EGX) Shariah-compliant stocks. You help users build optimized investment portfolios based on their preferences.

Your capabilities:
1. Help users invest in the EGX 33 Shariah Index stocks
2. Consider their budget, preferred stocks, and risk tolerance
3. Use AI-powered portfolio optimization

Available EGX 33 Shariah stocks:
ADIB.CA, SAUD.CA, AMOC.CA, ACGC.CA, ARCC.CA, CLHO.CA, SUGR.CA, EFID.CA, EFIH.CA, EGAL.CA, EGTS.CA, ETRS.CA, EMFD.CA, FAIT.CA, FAITA.CA, ISPH.CA, ICFC.CA, JUFO.CA, LCSW.CA, MASR.CA, MCQE.CA, ATQA.CA, MTIE.CA, EGAS.CA, OLFI.CA, ORAS.CA, ORHD.CA, ORWE.CA, PHDC.CA, SKPC.CA, OCDI.CA, TMGH.CA, ETEL.CA, RMDA.CA

When gathering information:
1. Ask for investment amount (in EGP or USD)
2. Ask if they have preferred stocks OR a risk profile (conservative/moderate/aggressive)
3. Be friendly, professional, and concise

When you have enough information, respond with a JSON block in this exact format:
```json
{
    "ready": true,
    "investment_amount": <number>,
    "preferred_stocks": ["TICKER1.CA", "TICKER2.CA"],
    "risk_profile": "conservative" | "moderate" | "aggressive" | null
}
```

If you don't have enough info, just chat normally to gather it."""


def consultant_node(state: AgentState) -> AgentState:
    """
    Chat with user and extract investment parameters.
    Uses LLM to understand user intent and extract entities.
    """
    llm = create_llm()
    
    # Build messages for LLM
    messages = [SystemMessage(content=CONSULTANT_SYSTEM_PROMPT)]
    messages.extend(state["messages"])
    
    # Get LLM response
    response = llm.invoke(messages)
    response_text = response.content
    
    # Try to extract JSON from response
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    
    new_state = state.copy()
    new_state["current_node"] = "consultant"
    
    if json_match:
        try:
            extracted = json.loads(json_match.group(1))
            
            if extracted.get("ready"):
                new_state["investment_amount"] = extracted.get("investment_amount")
                new_state["preferred_stocks"] = extracted.get("preferred_stocks", [])
                new_state["risk_profile"] = extracted.get("risk_profile")
                new_state["needs_info"] = False
                
                # Remove JSON from visible response
                clean_response = response_text.replace(json_match.group(0), "").strip()
                if not clean_response:
                    clean_response = "Great! I have all the information I need. Let me optimize your portfolio..."
                    
                new_state["messages"] = state["messages"] + [AIMessage(content=clean_response)]
            else:
                new_state["needs_info"] = True
                new_state["messages"] = state["messages"] + [AIMessage(content=response_text)]
                
        except json.JSONDecodeError:
            new_state["needs_info"] = True
            new_state["messages"] = state["messages"] + [AIMessage(content=response_text)]
    else:
        new_state["needs_info"] = True
        new_state["messages"] = state["messages"] + [AIMessage(content=response_text)]
    
    return new_state


def validator_node(state: AgentState) -> AgentState:
    """
    Validate the extracted information.
    Check if tickers are valid EGX 33 stocks.
    """
    new_state = state.copy()
    new_state["current_node"] = "validator"
    
    data_loader = get_data_loader()
    valid_tickers = data_loader.get_valid_tickers()
    
    # Validate investment amount
    if not state["investment_amount"] or state["investment_amount"] <= 0:
        new_state["error"] = "Please provide a valid investment amount greater than 0."
        new_state["needs_info"] = True
        return new_state
    
    # Validate tickers if provided
    if state["preferred_stocks"]:
        invalid_tickers = [t for t in state["preferred_stocks"] if t not in valid_tickers]
        
        if invalid_tickers:
            new_state["error"] = f"Invalid tickers: {', '.join(invalid_tickers)}. Please choose from the EGX 33 Shariah stocks."
            new_state["needs_info"] = True
            return new_state
    
    # Validate risk profile if no stocks specified
    if not state["preferred_stocks"] and not state["risk_profile"]:
        new_state["error"] = "Please specify either preferred stocks or a risk profile (conservative, moderate, or aggressive)."
        new_state["needs_info"] = True
        return new_state
    
    new_state["error"] = None
    new_state["needs_info"] = False
    
    return new_state


def optimizer_node(state: AgentState) -> AgentState:
    """
    Run portfolio optimization using the LSTM model and Mean-Variance Optimization.
    """
    new_state = state.copy()
    new_state["current_node"] = "optimizer"
    
    optimizer = get_optimizer()
    
    # Get stocks to optimize
    if state["preferred_stocks"]:
        tickers = state["preferred_stocks"]
    elif state["risk_profile"]:
        tickers = optimizer.get_stocks_by_risk_profile(state["risk_profile"])
    else:
        # Default to top 5 by recent performance
        tickers = optimizer.data_loader.get_valid_tickers()[:5]
    
    # Run optimization
    try:
        result = optimizer.optimize_portfolio(
            tickers=tickers,
            investment_amount=state["investment_amount"]
        )
        
        if "error" in result:
            new_state["error"] = result["error"]
        else:
            new_state["allocation"] = result
            
    except Exception as e:
        new_state["error"] = f"Optimization failed: {str(e)}"
    
    return new_state


def summary_node(state: AgentState) -> AgentState:
    """
    Format the optimization results into a natural language response.
    """
    new_state = state.copy()
    new_state["current_node"] = "summary"
    
    if state["error"]:
        error_msg = f"I encountered an issue: {state['error']}\n\nPlease try again with different parameters."
        new_state["messages"] = state["messages"] + [AIMessage(content=error_msg)]
        return new_state
    
    if not state["allocation"]:
        new_state["messages"] = state["messages"] + [AIMessage(content="I couldn't generate an allocation. Please try again.")]
        return new_state
    
    alloc = state["allocation"]
    
    # Build summary message
    summary_parts = [
        "## Your Optimized Shariah Portfolio\n",
        f"**Investment Amount:** {alloc['investment_amount']:,.2f} EGP\n",
        "\n### Portfolio Allocation\n",
        "| Ticker | Company | Weight | Amount (EGP) |",
        "|--------|---------|--------|--------------|"
    ]
    
    for ticker, amount in sorted(alloc["allocation"].items(), key=lambda x: x[1], reverse=True):
        weight = alloc["weights"][ticker]
        company_name = TICKER_NAMES.get(ticker, ticker)
        summary_parts.append(f"| {ticker} | {company_name} | {weight*100:.1f}% | {amount:,.2f} |")
    
    # Calculate risk-adjusted interpretation
    expected_return = alloc['expected_return'] * 100
    volatility = alloc['expected_volatility'] * 100
    sharpe = alloc['sharpe_ratio']
    
    # Risk level interpretation
    if volatility < 15:
        risk_level = "Low"
        risk_desc = "relatively stable with smaller price swings"
    elif volatility < 25:
        risk_level = "Moderate"
        risk_desc = "balanced between stability and growth potential"
    else:
        risk_level = "High"
        risk_desc = "more volatile but with higher growth potential"
    
    # Sharpe interpretation
    if sharpe < 0.5:
        sharpe_desc = "The risk-adjusted return is below average. Consider a more conservative allocation."
    elif sharpe < 1.0:
        sharpe_desc = "The portfolio offers reasonable risk-adjusted returns."
    else:
        sharpe_desc = "Excellent risk-adjusted returns - the portfolio is well-optimized."
    
    summary_parts.extend([
        "\n### Portfolio Metrics & What They Mean\n",
        f"**Expected Return: {expected_return:.2f}%**",
        f"> This is the predicted annual return based on our AI model's analysis of historical patterns. "
        f"If this holds, a {alloc['investment_amount']:,.0f} EGP investment could grow to approximately "
        f"{alloc['investment_amount'] * (1 + alloc['expected_return']):,.0f} EGP over one year.\n",
        f"**Expected Volatility: {volatility:.2f}% ({risk_level} Risk)**",
        f"> Volatility measures how much the portfolio value may fluctuate. "
        f"This portfolio is {risk_desc}. Expect daily swings of roughly {volatility/16:.1f}% on average.\n",
        f"**Sharpe Ratio: {sharpe:.2f}**",
        f"> The Sharpe Ratio measures return per unit of risk. Higher is better (above 1.0 is excellent). "
        f"{sharpe_desc}\n",
        "---",
        "*This portfolio is optimized using AI-powered predictions and Mean-Variance Optimization, focusing on Shariah-compliant EGX stocks. Past performance does not guarantee future results.*",
        "\nWould you like me to adjust anything or create a different portfolio?"
    ])
    
    summary_message = "\n".join(summary_parts)
    new_state["messages"] = state["messages"] + [AIMessage(content=summary_message)]
    
    return new_state


def route_after_consultant(state: AgentState) -> Literal["validator", "end"]:
    """Decide where to go after consultant node."""
    if state.get("needs_info", True):
        return "end"  # Wait for more user input
    return "validator"


def route_after_validator(state: AgentState) -> Literal["consultant", "optimizer"]:
    """Decide where to go after validator node."""
    if state.get("error"):
        return "consultant"  # Go back to fix errors
    return "optimizer"


def create_agent_graph() -> StateGraph:
    """Create and return the LangGraph agent."""
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("consultant", consultant_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("optimizer", optimizer_node)
    workflow.add_node("summary", summary_node)
    
    # Set entry point
    workflow.set_entry_point("consultant")
    
    # Add edges
    workflow.add_conditional_edges(
        "consultant",
        route_after_consultant,
        {
            "validator": "validator",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "consultant": "consultant",
            "optimizer": "optimizer"
        }
    )
    
    workflow.add_edge("optimizer", "summary")
    workflow.add_edge("summary", END)
    
    return workflow.compile()


class PortfolioAgent:
    """High-level agent interface for the web application."""
    
    def __init__(self):
        self.graph = create_agent_graph()
        self.state: AgentState = {
            "messages": [],
            "investment_amount": None,
            "preferred_stocks": [],
            "risk_profile": None,
            "allocation": None,
            "error": None,
            "current_node": "",
            "needs_info": True
        }
    
    def reset(self):
        """Reset the conversation state."""
        self.state = {
            "messages": [],
            "investment_amount": None,
            "preferred_stocks": [],
            "risk_profile": None,
            "allocation": None,
            "error": None,
            "current_node": "",
            "needs_info": True
        }
    
    async def chat(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.
        """
        # Add user message to state
        self.state["messages"].append(HumanMessage(content=user_message))
        
        # Run the graph
        result = self.graph.invoke(self.state)
        
        # Update state
        self.state = result
        
        # Return the last AI message
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                return msg.content
        
        return "I'm processing your request..."
    
    def get_last_response(self) -> str:
        """Get the last AI response."""
        for msg in reversed(self.state["messages"]):
            if isinstance(msg, AIMessage):
                return msg.content
        return ""
