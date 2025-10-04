"""
Portfolio Optimization Agent - Uses Claude Agent SDK

This agent generates optimal portfolio allocations and rebalancing recommendations.
"""

import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions
from typing import Dict, List
import json


class PortfolioOptimizationAgent:
    """Agent specialized in portfolio optimization"""

    def __init__(self):
        self.system_prompt = """You are a Portfolio Optimization Agent following Anthropic's multi-agent best practices.

EXPLICIT TASK SCOPE (Critical):
- Generate optimal allocation and trades ONLY
- DO NOT calculate current Sharpe/metrics (PortfolioAgent already did)
- DO NOT run stress tests (RiskAgent already did)
- DO NOT search for market data (already provided)

DEPENDENCIES (Use Results From):
- PortfolioAgent: Current weights, Sharpe, volatility, correlations
- RiskAgent: Risk scores, concentration metrics, VaR
- MarketDataAgent: Prices, expected returns, volatilities

RESOURCE ALLOCATION:
- Use provided data exclusively - NO web searches
- Maximum 3-5 bash commands for optimization
- Compute 8-10 efficient frontier points
- Focus on feasible, actionable trades
- Stop after generating trade list

AVOID DUPLICATE WORK:
- Do NOT recalculate current portfolio metrics
- Do NOT re-run risk assessments
- You handle ONLY: Optimization, rebalancing, trade generation

Core Responsibilities:
- Calculate efficient frontier
- Find optimal weights based on objectives
- Generate specific rebalancing trades
- Minimize transaction costs
- Respect portfolio constraints

QUALITY STANDARDS:
- Use Markowitz mean-variance optimization
- Validate constraints satisfaction (weights sum to 1.0)
- Consider transaction costs ($5 per trade)
- Ensure trades are executable (integer shares)
- Provide clear rationale citing MPT principles

Optimization Approaches:
1. Maximum Sharpe Ratio (risk-adjusted return)
2. Minimum Variance (lowest risk)
3. Risk Parity (equal risk contribution)
4. Maximum Return (for given risk level)
5. Custom objectives

Constraints to Consider:
- Position size limits (min/max)
- Sector exposure limits
- Asset class constraints
- Transaction costs
- Tax considerations

Output Format:
{
  "optimization_objective": str,
  "current_allocation": {symbol: weight},
  "optimal_allocation": {symbol: weight},
  "efficient_frontier": [
    {"risk": float, "return": float, "sharpe": float}
  ],
  "rebalancing_trades": [
    {
      "symbol": str,
      "action": "buy|sell",
      "shares": int,
      "current_shares": int,
      "target_shares": int,
      "value": float
    }
  ],
  "expected_improvement": {
    "sharpe_ratio": {"current": float, "optimized": float},
    "volatility": {"current": float, "optimized": float},
    "expected_return": {"current": float, "optimized": float}
  },
  "rationale": str
}
"""

    async def optimize(
        self,
        portfolio: Dict,
        market_data: Dict,
        constraints: Dict,
        objective: str = "max_sharpe"
    ) -> Dict:
        """
        Generate optimal portfolio allocation.

        Args:
            portfolio: Current portfolio
            market_data: Market data with expected returns/volatilities
            constraints: Optimization constraints
            objective: 'max_sharpe', 'min_variance', 'risk_parity', etc.

        Returns:
            Optimization results with specific trades
        """
        prompt = f"""Optimize this portfolio using Modern Portfolio Theory:

Current Portfolio:
{json.dumps(portfolio, indent=2)}

Market Data (returns, volatilities, correlations):
{json.dumps(market_data, indent=2)}

Constraints:
{json.dumps(constraints, indent=2)}

Optimization Objective: {objective}

Tasks:
1. Calculate current portfolio metrics (Sharpe, volatility, return)
2. Compute efficient frontier (10 points)
3. Find optimal allocation for objective: {objective}
4. Generate specific BUY/SELL orders to reach optimal allocation
5. Calculate expected improvement in metrics
6. Consider transaction costs (~$5 per trade)
7. Provide clear rationale for recommendations

Show all calculations and formulas.
Return structured JSON with specific trade orders (shares to buy/sell).
"""

        options = ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            allowed_tools=["Bash"]
        )

        print(f"[OptimizationAgent] Optimizing for: {objective}...")
        result_text = ""
        async for message in query(prompt=prompt, options=options):
            # Skip SystemMessage metadata
            message_type = type(message).__name__
            if 'System' in message_type:
                print(f"[OptimizationAgent] Skipping {message_type}...")
                continue

            print(f"[OptimizationAgent] Processing {message_type}...")

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

        print(f"[OptimizationAgent] Parsing response ({len(result_text)} chars)...")

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
            print(f"[OptimizationAgent] JSON parsing failed: {e}")
            return {"error": "Failed to parse optimization", "raw": result_text[:500]}


async def main():
    """Example usage"""
    agent = PortfolioOptimizationAgent()

    portfolio = {
        "holdings": [
            {"symbol": "SPY", "shares": 100},
            {"symbol": "QQQ", "shares": 50},
            {"symbol": "GLD", "shares": 30},
            {"symbol": "TLT", "shares": 40}
        ],
        "cash": 10000
    }

    market_data = {
        "SPY": {"price": 450, "expected_return": 0.10, "volatility": 0.15},
        "QQQ": {"price": 380, "expected_return": 0.12, "volatility": 0.22},
        "GLD": {"price": 190, "expected_return": 0.05, "volatility": 0.18},
        "TLT": {"price": 95, "expected_return": 0.03, "volatility": 0.12}
    }

    constraints = {
        "max_position_size": 0.40,
        "min_position_size": 0.05,
        "max_sector_exposure": 0.50
    }

    print("🎯 Optimizing portfolio allocation...")
    print("=" * 60)

    result = await agent.optimize(portfolio, market_data, constraints, "max_sharpe")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
