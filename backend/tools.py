"""
ShariahFolio Tools Module
LangChain tools for portfolio optimization and stock information.

These tools are used by the LangGraph agent to perform actual operations
rather than hallucinating results.
"""

import json
import logging
from typing import Optional, List, Union
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from .portfolio_model import get_optimizer
from .data_loader import get_data_loader
from .config import TICKER_NAMES, TICKER_SECTORS, RISK_PROFILES

# Configure logger
logger = logging.getLogger(__name__)


# =============================================================================
# TOOL INPUT SCHEMAS
# =============================================================================

class OptimizePortfolioInput(BaseModel):
    """Input schema for portfolio optimization tool."""
    investment_amount: float = Field(
        description="The amount to invest in EGP (Egyptian Pounds). Must be a positive number."
    )
    tickers: Optional[Union[List[str], str]] = Field(
        default=None,
        description="List of specific ticker symbols to include (e.g., ['ETEL.CA', 'EFIH.CA']). Can be used alone or combined with risk_profile."
    )
    risk_profile: Optional[str] = Field(
        default=None,
        description="Risk profile for automatic stock selection: 'conservative', 'moderate', or 'aggressive'. Can be combined with tickers to add specific stocks to the risk-based selection."
    )


class GetStockInfoInput(BaseModel):
    """Input schema for stock info tool."""
    ticker: str = Field(
        description="The ticker symbol to get information for (e.g., 'ETEL.CA')"
    )


class GetStocksByRiskInput(BaseModel):
    """Input schema for getting stocks by risk profile."""
    risk_profile: str = Field(
        description="Risk profile: 'conservative', 'moderate', or 'aggressive'"
    )


# =============================================================================
# TOOLS
# =============================================================================

@tool(args_schema=OptimizePortfolioInput)
def optimize_portfolio(
    investment_amount: float,
    tickers: Optional[Union[List[str], str]] = None,
    risk_profile: Optional[str] = None
) -> str:
    """
    Optimize a Shariah-compliant portfolio using LSTM predictions and Mean-Variance Optimization.

    This tool trains LSTM models to predict stock returns, then uses Mean-Variance Optimization
    to find the optimal allocation that maximizes the Sharpe ratio.

    You MUST call this tool to generate portfolio allocations. Do not make up allocation numbers.

    IMPORTANT: You can combine both tickers AND risk_profile to include specific stocks
    along with the risk-based stock selection. For example, if the user wants a moderate
    portfolio but also wants to include ETEL.CA, provide both risk_profile="moderate"
    and tickers=["ETEL.CA"].

    Args:
        investment_amount: Amount to invest in EGP (must be positive)
        tickers: Optional list of specific tickers to include (can be combined with risk_profile)
        risk_profile: Optional risk profile ('conservative', 'moderate', 'aggressive')

    Returns:
        Formatted string with portfolio allocation, weights, and metrics
    """
    logger.info(f"=" * 60)
    logger.info(f"Tool called: optimize_portfolio")
    logger.info(f"  - investment_amount: {investment_amount} (type: {type(investment_amount).__name__})")
    logger.info(f"  - tickers: {tickers} (type: {type(tickers).__name__ if tickers else 'None'})")
    logger.info(f"  - risk_profile: {risk_profile} (type: {type(risk_profile).__name__ if risk_profile else 'None'})")

    # Handle tickers parameter - LLMs sometimes pass it as a JSON string instead of a list
    if tickers is not None and isinstance(tickers, str):
        logger.info(f"Converting tickers from string: {tickers}")
        try:
            # Try to parse as JSON array
            parsed_tickers = json.loads(tickers)
            if isinstance(parsed_tickers, list):
                tickers = parsed_tickers
            else:
                # Single ticker passed as string
                tickers = [tickers]
        except json.JSONDecodeError:
            # Not JSON, treat as comma-separated or single ticker
            if ',' in tickers:
                tickers = [t.strip() for t in tickers.split(',')]
            else:
                tickers = [tickers.strip()]
        logger.info(f"Converted tickers to list: {tickers}")

    # Validate inputs
    if investment_amount <= 0:
        error_msg = "Error: Investment amount must be a positive number."
        logger.error(f"Validation failed: {error_msg}")
        return error_msg

    if not tickers and not risk_profile:
        error_msg = "Error: You must provide either specific tickers, a risk profile, or both."
        logger.error(f"Validation failed: {error_msg}")
        return error_msg

    if risk_profile and risk_profile.lower() not in RISK_PROFILES:
        error_msg = f"Error: Invalid risk profile '{risk_profile}'. Must be 'conservative', 'moderate', or 'aggressive'."
        logger.error(f"Validation failed: {error_msg}")
        return error_msg

    # Get optimizer and data loader
    optimizer = get_optimizer()
    data_loader = get_data_loader()
    valid_tickers = data_loader.get_valid_tickers()

    # Build the ticker list - combining risk profile stocks with any additional specified tickers
    selected_tickers = set()

    # First, add stocks from risk profile if provided
    if risk_profile:
        risk_profile_lower = risk_profile.lower()
        profile_tickers = optimizer.get_stocks_by_risk_profile(risk_profile_lower)
        selected_tickers.update(profile_tickers)
        logger.info(f"Added {len(profile_tickers)} tickers from {risk_profile} profile: {profile_tickers}")

    # Then, add any specific tickers requested by the user
    if tickers:
        # Normalize tickers
        normalized_tickers = []
        for t in tickers:
            ticker = t.strip().upper()
            if not ticker.endswith(".CA"):
                ticker = f"{ticker}.CA"
            normalized_tickers.append(ticker)

        # Validate provided tickers
        invalid = [t for t in normalized_tickers if t not in valid_tickers]
        if invalid:
            return f"Error: Invalid tickers: {', '.join(invalid)}. These are not available in the EGX 33 Shariah Index. Use `list_available_stocks` to see valid options."

        selected_tickers.update(normalized_tickers)
        logger.info(f"Added {len(normalized_tickers)} specific tickers: {normalized_tickers}")

    # Convert to sorted list for consistency
    selected_tickers = sorted(list(selected_tickers))

    if len(selected_tickers) == 0:
        error_msg = "Error: No valid tickers found for optimization."
        logger.error(f"Validation failed: {error_msg}")
        return error_msg

    logger.info(f"Final ticker list ({len(selected_tickers)} stocks): {selected_tickers}")

    # Run optimization
    try:
        logger.info("Starting portfolio optimization...")
        result = optimizer.optimize_portfolio(
            tickers=selected_tickers,
            investment_amount=investment_amount
        )
        logger.info(f"Optimization returned: {list(result.keys()) if isinstance(result, dict) else type(result)}")

        if "error" in result:
            error_msg = f"Error during optimization: {result['error']}"
            logger.error(f"Optimizer error: {error_msg}")
            return error_msg

        # Build description of what was optimized
        optimization_desc = []
        if risk_profile:
            optimization_desc.append(f"**Risk Profile:** {risk_profile.title()}")
        if tickers:
            optimization_desc.append(f"**Additional Stocks Included:** {', '.join(tickers)}")

        # Format the result
        output_parts = [
            "## Portfolio Optimization Results\n",
            f"**Investment Amount:** {result['investment_amount']:,.2f} EGP",
        ]
        output_parts.extend(optimization_desc)
        output_parts.extend([
            f"**Stocks Analyzed:** {len(selected_tickers)}",
            f"**Stocks in Final Portfolio:** {len(result['allocation'])}",
            "\n### Allocation\n",
            "| Ticker | Company | Sector | Weight | Amount (EGP) |",
            "|--------|---------|--------|--------|--------------|"
        ])

        for ticker, amount in sorted(result["allocation"].items(), key=lambda x: x[1], reverse=True):
            weight = result["weights"][ticker]
            company = TICKER_NAMES.get(ticker, ticker)
            sector = TICKER_SECTORS.get(ticker, "Unknown")
            output_parts.append(f"| {ticker} | {company} | {sector} | {weight*100:.1f}% | {amount:,.2f} |")

        # Add metrics
        expected_return = result['expected_return'] * 100
        volatility = result['expected_volatility'] * 100
        sharpe = result['sharpe_ratio']

        # Risk level interpretation
        if volatility < 15:
            risk_level = "Low"
        elif volatility < 25:
            risk_level = "Moderate"
        else:
            risk_level = "High"

        output_parts.extend([
            "\n### Portfolio Metrics\n",
            f"| Metric | Value | Interpretation |",
            f"|--------|-------|----------------|",
            f"| Expected Annual Return | {expected_return:.2f}% | Predicted return based on LSTM model |",
            f"| Expected Volatility | {volatility:.2f}% | {risk_level} risk level |",
            f"| Sharpe Ratio | {sharpe:.2f} | {'Excellent' if sharpe > 1 else 'Good' if sharpe > 0.5 else 'Below average'} risk-adjusted return |",
            f"\n**Projected Value (1 year):** {result['investment_amount'] * (1 + result['expected_return']):,.2f} EGP"
        ])

        return "\n".join(output_parts)

    except Exception as e:
        error_msg = f"Error: Portfolio optimization failed - {str(e)}"
        logger.exception(f"Portfolio optimization failed: {e}")
        logger.error(f"Returning error: {error_msg}")
        return error_msg

    logger.info(f"Tool returning successful result ({len(output_parts)} lines)")
    logger.info(f"=" * 60)


@tool(args_schema=GetStockInfoInput)
def get_stock_info(ticker: str) -> str:
    """
    Get detailed information about a specific stock in the EGX 33 Shariah Index.

    Use this tool when the user asks about a specific stock's details, price, or volatility.

    Args:
        ticker: The ticker symbol (e.g., 'ETEL.CA')

    Returns:
        Formatted string with stock information
    """
    logger.info(f"Tool called: get_stock_info(ticker={ticker})")

    # Normalize ticker
    ticker = ticker.upper()
    if not ticker.endswith(".CA"):
        ticker = f"{ticker}.CA"

    data_loader = get_data_loader()

    # Check if valid
    if ticker not in data_loader.ticker_data:
        return f"Error: Ticker '{ticker}' not found in the EGX 33 Shariah Index."

    # Get info
    info = data_loader.get_ticker_info(ticker)
    if not info:
        return f"Error: Could not retrieve information for '{ticker}'."

    company = TICKER_NAMES.get(ticker, ticker)
    sector = TICKER_SECTORS.get(ticker, "Unknown")

    # Handle potential None values
    latest_price = info.get('latest_price')
    volatility = info.get('volatility_30d')
    data_points = info.get('data_points', 0)
    date_range = info.get('date_range', {})

    price_str = f"{latest_price:,.2f} EGP" if latest_price is not None else "N/A"
    vol_str = f"{volatility*100:.2f}%" if volatility is not None else "N/A"
    start_date = date_range.get('start', '')[:10] if date_range.get('start') else "N/A"
    end_date = date_range.get('end', '')[:10] if date_range.get('end') else "N/A"

    output = f"""## {ticker} - {company}

**Sector:** {sector}

### Market Data
| Metric | Value |
|--------|-------|
| Latest Price | {price_str} |
| 30-Day Volatility | {vol_str} |
| Data Points | {data_points} |
| Data Range | {start_date} to {end_date} |
"""

    return output


@tool
def list_available_stocks() -> str:
    """
    List all available stocks in the EGX 33 Shariah Index.

    Use this tool when the user wants to see what stocks are available for investment.

    Returns:
        Formatted table of all available Shariah-compliant stocks
    """
    logger.info("Tool called: list_available_stocks()")

    data_loader = get_data_loader()
    valid_tickers = data_loader.get_valid_tickers()
    volatilities = data_loader.get_ticker_volatility()
    prices = data_loader.get_latest_prices(valid_tickers)

    output_parts = [
        "## EGX 33 Shariah Index Stocks\n",
        f"**Total Available:** {len(valid_tickers)} stocks\n",
        "| Ticker | Company | Sector | Latest Price | Volatility |",
        "|--------|---------|--------|--------------|------------|"
    ]

    for ticker in sorted(valid_tickers):
        company = TICKER_NAMES.get(ticker, ticker)
        sector = TICKER_SECTORS.get(ticker, "Unknown")
        price = prices.get(ticker, 0)
        vol = volatilities.get(ticker, 0)

        price_str = f"{price:,.2f} EGP" if price else "N/A"
        vol_str = f"{vol*100:.1f}%" if vol else "N/A"

        output_parts.append(f"| {ticker} | {company} | {sector} | {price_str} | {vol_str} |")

    output_parts.append("\n*Volatility shown is 30-day historical volatility*")

    return "\n".join(output_parts)


@tool(args_schema=GetStocksByRiskInput)
def get_stocks_by_risk_profile(risk_profile: str) -> str:
    """
    Get recommended stocks based on a risk profile.

    Use this tool to show the user which stocks would be selected for a given risk level
    before actually running the optimization.

    Args:
        risk_profile: 'conservative', 'moderate', or 'aggressive'

    Returns:
        List of stocks that match the risk profile
    """
    logger.info(f"Tool called: get_stocks_by_risk_profile(risk={risk_profile})")

    risk_profile = risk_profile.lower()

    if risk_profile not in RISK_PROFILES:
        return f"Error: Invalid risk profile '{risk_profile}'. Must be 'conservative', 'moderate', or 'aggressive'."

    optimizer = get_optimizer()
    tickers = optimizer.get_stocks_by_risk_profile(risk_profile)

    profile_info = RISK_PROFILES[risk_profile]

    output_parts = [
        f"## {risk_profile.title()} Risk Profile\n",
        f"**Description:** {profile_info['description']}",
        f"**Recommended Stocks:** {len(tickers)}\n",
        "| Ticker | Company | Sector |",
        "|--------|---------|--------|"
    ]

    for ticker in tickers:
        company = TICKER_NAMES.get(ticker, ticker)
        sector = TICKER_SECTORS.get(ticker, "Unknown")
        output_parts.append(f"| {ticker} | {company} | {sector} |")

    return "\n".join(output_parts)


# =============================================================================
# TOOL COLLECTION
# =============================================================================

def get_portfolio_tools() -> list:
    """
    Get all portfolio-related tools for the agent.

    Returns:
        List of LangChain tools
    """
    return [
        optimize_portfolio,
        get_stock_info,
        list_available_stocks,
        get_stocks_by_risk_profile
    ]


# Tool descriptions for the system prompt
TOOL_DESCRIPTIONS = """
## Available Tools

You have access to the following tools:

### 1. optimize_portfolio
**Purpose:** Create an optimized portfolio allocation using LSTM predictions and Mean-Variance Optimization.
**When to use:** When the user wants to invest money and you have:
- An investment amount, AND
- Either specific stock tickers, a risk profile, OR BOTH (to combine them)
**IMPORTANT:**
- Always use this tool to generate portfolio allocations. Never make up numbers.
- You CAN provide BOTH tickers AND risk_profile to include specific stocks along with risk-based selection.
  For example: If user wants "moderate risk but also include ETEL.CA", use:
  investment_amount=100000, risk_profile="moderate", tickers=["ETEL.CA"]

### 2. get_stock_info
**Purpose:** Get detailed information about a specific stock.
**When to use:** When the user asks about a particular stock's price, volatility, or details.

### 3. list_available_stocks
**Purpose:** Show all available Shariah-compliant stocks in the EGX 33 Index.
**When to use:** When the user wants to see available investment options.

### 4. get_stocks_by_risk_profile
**Purpose:** Show which stocks would be selected for a given risk level.
**When to use:** When the user wants to understand what stocks match their risk tolerance before investing.
"""
