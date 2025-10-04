"""
Portfolio Analysis Agent - Uses Claude Agent SDK

This agent performs quantitative portfolio analysis and calculates risk metrics.
"""

import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions
from typing import Dict
import json


class PortfolioAnalysisAgent:
    """Agent specialized in portfolio quantitative analysis"""

    def __init__(self):
        self.system_prompt = """You are a Quantitative Portfolio Analysis Agent following Anthropic's multi-agent best practices.

EXPLICIT TASK SCOPE (Critical):
- Calculate MPT metrics ONLY
- DO NOT assess risks (RiskAgent's job)
- DO NOT optimize allocation (OptimizationAgent's job)
- DO NOT search for external data (already provided)

RESOURCE ALLOCATION:
- Use provided market data - NO web searches
- Maximum 2-3 bash calculations if needed
- Focus on accuracy over exhaustive analysis
- Stop when core metrics computed

AVOID DUPLICATE WORK:
- RiskAgent handles: VaR, CVaR, stress tests
- OptimizationAgent handles: rebalancing, efficient frontier
- You handle ONLY: Sharpe, volatility, correlations, weights

Core Responsibilities:
- Calculate portfolio value and position weights
- Compute risk-adjusted returns (Sharpe, Sortino, Calmar ratios)
- Analyze diversification using correlation matrices
- Perform attribution analysis
- Calculate volatility and drawdown metrics

QUALITY STANDARDS:
- Show all formulas and calculations
- Use industry-standard methodologies (MPT)
- Validate calculations (e.g., weights sum to 1.0)
- Flag any data quality concerns

Output Format:
Return structured JSON with:
{
  "portfolio_value": {
    "total": float,
    "positions": [{symbol, value, weight, shares}],
    "cash": float
  },
  "performance_metrics": {
    "sharpe_ratio": float,
    "sortino_ratio": float,
    "max_drawdown_pct": float,
    "volatility_annual": float,
    "total_return_pct": float
  },
  "diversification": {
    "correlation_matrix": {},
    "effective_n_positions": float,
    "sector_exposure": {}
  },
  "attribution": {
    "top_contributors": [],
    "top_detractors": []
  }
}
"""

    async def analyze(self, portfolio: Dict, market_data: Dict) -> Dict:
        """
        Analyze portfolio using quantitative methods.

        Args:
            portfolio: Portfolio holdings and cash
            market_data: Current market prices and data

        Returns:
            Comprehensive portfolio analysis
        """
        prompt = f"""Analyze this portfolio using Modern Portfolio Theory:

Portfolio:
{json.dumps(portfolio, indent=2)}

Current Market Data:
{json.dumps(market_data, indent=2)}

Tasks:
1. Calculate total portfolio value and position weights
2. Compute Sharpe ratio (assume 4% risk-free rate)
3. Calculate annualized volatility
4. Estimate max drawdown (use historical volatility)
5. Build correlation matrix between holdings
6. Calculate effective number of positions (1/HHI)
7. Analyze sector exposure
8. Identify top/bottom contributors to returns

Show your calculations and formulas used.
Return results as structured JSON matching the specified format.
"""

        options = ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            allowed_tools=["Bash"]  # Can run Python calculations
        )

        print(f"[PortfolioAgent] Analyzing portfolio with {len(portfolio.get('holdings', []))} holdings...")
        result_text = ""
        async for message in query(prompt=prompt, options=options):
            # Skip SystemMessage metadata
            message_type = type(message).__name__
            if 'System' in message_type:
                print(f"[PortfolioAgent] Skipping {message_type}...")
                continue

            print(f"[PortfolioAgent] Processing {message_type}...")

            # Extract content from Message objects
            raw_content = None
            if hasattr(message, 'result'):
                raw_content = message.result
            elif hasattr(message, 'content'):
                raw_content = message.content
            else:
                raw_content = message

            # Extract text from blocks
            if isinstance(raw_content, list):
                for block in raw_content:
                    # Only extract from TextBlock, skip ToolUseBlock
                    if hasattr(block, 'text'):
                        result_text += block.text + "\n"
            elif raw_content:
                result_text += str(raw_content) + "\n"

        print(f"[PortfolioAgent] Parsing response ({len(result_text)} chars)...")

        try:
            # Extract JSON from markdown code blocks
            if "```json" in result_text:
                start = result_text.find("```json") + 7
                end = result_text.find("```", start)
                json_str = result_text[start:end].strip()
                return json.loads(json_str)
            else:
                # Try to parse directly
                return json.loads(result_text)
        except json.JSONDecodeError as e:
            print(f"[PortfolioAgent] JSON parsing failed: {e}")
            return {"error": "Failed to parse analysis", "raw": result_text[:500]}


async def main():
    """Example usage"""
    agent = PortfolioAnalysisAgent()

    portfolio = {
        "holdings": [
            {"symbol": "SPY", "shares": 100},
            {"symbol": "QQQ", "shares": 50},
            {"symbol": "GLD", "shares": 30}
        ],
        "cash": 10000
    }

    market_data = {
        "SPY": {"price": 450.00, "change_pct": 0.5},
        "QQQ": {"price": 380.00, "change_pct": -0.3},
        "GLD": {"price": 190.00, "change_pct": 1.2}
    }

    print("📊 Analyzing portfolio...")
    print("=" * 60)

    analysis = await agent.analyze(portfolio, market_data)
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
