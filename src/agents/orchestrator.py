"""
Multi-Agent Portfolio Manager Orchestrator

This orchestrator coordinates specialized agents using Claude Code's Task tool
to perform parallel portfolio analysis, market research, and risk assessment.
"""

import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime


class PortfolioOrchestrator:
    """
    Orchestrates multiple specialized agents for portfolio management.
    Uses Claude Code to launch agents in parallel for different tasks.
    """

    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {}

    def create_market_data_agent_prompt(self, symbols: List[str]) -> str:
        """Generate prompt for market data collection agent"""
        return f"""You are a Market Data Collection Agent.

Your task is to gather current market data for the following symbols: {', '.join(symbols)}

For each symbol, collect:
1. Current price and daily change
2. Volume and market cap
3. 52-week high/low
4. Key financial ratios (P/E, P/B, etc.)
5. Recent news (last 7 days)
6. Analyst ratings and price targets

Use web search to find the most recent data from reliable financial sources.
Format your output as a structured JSON report with all the data organized by symbol.

Return ONLY the JSON data without any additional explanation."""

    def create_portfolio_analysis_agent_prompt(self, portfolio: Dict, market_data: Optional[str] = None) -> str:
        """Generate prompt for portfolio analysis agent"""
        return f"""You are a Portfolio Analysis Agent specializing in quantitative analysis.

Portfolio to analyze:
{json.dumps(portfolio, indent=2)}

{f"Market Data Available: {market_data}" if market_data else "Please gather current market data first."}

Your task:
1. Calculate current portfolio value and allocation percentages
2. Compute risk metrics: Sharpe ratio, maximum drawdown, volatility
3. Calculate correlation matrix between assets
4. Identify concentration risks
5. Compute sector/asset class exposure
6. Provide performance attribution analysis

Use Modern Portfolio Theory principles.
Return a detailed JSON report with all calculations and metrics."""

    def create_risk_assessment_agent_prompt(self, portfolio: Dict, market_conditions: str = "") -> str:
        """Generate prompt for risk assessment agent"""
        return f"""You are a Risk Assessment Agent specializing in portfolio risk analysis.

Portfolio:
{json.dumps(portfolio, indent=2)}

Current Market Conditions: {market_conditions}

Your task:
1. Identify and quantify key risks (market, concentration, sector, geopolitical)
2. Stress test portfolio under various scenarios (recession, inflation spike, market crash)
3. Evaluate downside protection and tail risk
4. Assess liquidity risk
5. Calculate Value at Risk (VaR) and Conditional VaR
6. Provide risk mitigation recommendations

Use quantitative risk models and current market analysis.
Return a comprehensive risk report in JSON format with specific risk scores and recommendations."""

    def create_optimization_agent_prompt(self, portfolio: Dict, constraints: Dict, objectives: List[str]) -> str:
        """Generate prompt for portfolio optimization agent"""
        return f"""You are a Portfolio Optimization Agent using Modern Portfolio Theory.

Current Portfolio:
{json.dumps(portfolio, indent=2)}

Constraints:
{json.dumps(constraints, indent=2)}

Optimization Objectives: {', '.join(objectives)}

Your task:
1. Calculate efficient frontier
2. Find optimal allocation based on objectives (max Sharpe, min variance, etc.)
3. Propose rebalancing recommendations with specific trades
4. Calculate expected improvement in risk-adjusted returns
5. Provide alternative allocation scenarios
6. Include transaction cost considerations

Return detailed optimization results in JSON format with:
- Recommended allocations (percentages and share quantities)
- Expected metrics improvement
- Specific buy/sell orders
- Rationale for each recommendation"""

    def create_market_outlook_agent_prompt(self, sectors: List[str], timeframe: str = "3-6 months") -> str:
        """Generate prompt for market outlook agent"""
        return f"""You are a Market Outlook Agent providing forward-looking analysis.

Focus Sectors: {', '.join(sectors)}
Timeframe: {timeframe}

Your task:
1. Analyze current macroeconomic conditions (inflation, rates, GDP growth)
2. Research sector-specific trends and catalysts
3. Review expert forecasts from major institutions
4. Identify emerging risks and opportunities
5. Provide sector rotation recommendations
6. Include geopolitical and regulatory considerations

Use web search extensively to gather current market views from multiple sources.
Cite all sources and distinguish between factual data and forecasts.
Return a comprehensive market outlook report in JSON format."""

    async def run_parallel_analysis(self, portfolio: Dict, symbols: List[str]) -> Dict:
        """
        Coordinate parallel execution of multiple agents.

        This method would integrate with Claude Code's Task tool to launch
        multiple agents simultaneously.
        """
        print(f"\n{'='*60}")
        print(f"Portfolio Manager Multi-Agent System - Session {self.session_id}")
        print(f"{'='*60}\n")

        # Phase 1: Data Collection (parallel)
        print("Phase 1: Launching data collection agents...")
        market_data_prompt = self.create_market_data_agent_prompt(symbols)

        # Phase 2: Analysis (parallel after data collection)
        print("\nPhase 2: Launching analysis agents in parallel...")
        portfolio_analysis_prompt = self.create_portfolio_analysis_agent_prompt(portfolio)
        risk_assessment_prompt = self.create_risk_assessment_agent_prompt(portfolio)

        # Phase 3: Optimization and Outlook (parallel)
        print("\nPhase 3: Launching optimization and outlook agents...")
        optimization_prompt = self.create_optimization_agent_prompt(
            portfolio,
            constraints={"max_position_size": 0.20, "min_position_size": 0.02},
            objectives=["maximize Sharpe ratio", "minimize drawdown"]
        )

        sectors = list(set([asset.get('sector', 'Unknown') for asset in portfolio.get('holdings', [])]))
        market_outlook_prompt = self.create_market_outlook_agent_prompt(sectors)

        return {
            "session_id": self.session_id,
            "agents": {
                "market_data": {"prompt": market_data_prompt, "status": "ready"},
                "portfolio_analysis": {"prompt": portfolio_analysis_prompt, "status": "ready"},
                "risk_assessment": {"prompt": risk_assessment_prompt, "status": "ready"},
                "optimization": {"prompt": optimization_prompt, "status": "ready"},
                "market_outlook": {"prompt": market_outlook_prompt, "status": "ready"}
            },
            "instructions": """
To execute this multi-agent system with Claude Code:

1. Save the agent prompts from the output above
2. Use Claude Code's Task tool to launch agents in parallel
3. Each agent will work independently on its specialized task
4. Combine results for comprehensive portfolio analysis

Example Claude Code usage:
- Launch market_data and market_outlook agents first (they need web access)
- Then launch portfolio_analysis, risk_assessment, and optimization agents in parallel
- Consolidate all results for final recommendations
"""
        }


def main():
    """Example usage of the orchestrator"""

    # Example portfolio
    example_portfolio = {
        "holdings": [
            {"symbol": "SPY", "shares": 100, "sector": "Broad Market ETF"},
            {"symbol": "QQQ", "shares": 50, "sector": "Technology"},
            {"symbol": "GLD", "shares": 30, "sector": "Precious Metals"},
            {"symbol": "TLT", "shares": 40, "sector": "Bonds"},
        ],
        "cash": 10000
    }

    symbols = [holding["symbol"] for holding in example_portfolio["holdings"]]

    orchestrator = PortfolioOrchestrator()

    # Generate all agent prompts
    result = asyncio.run(orchestrator.run_parallel_analysis(example_portfolio, symbols))

    # Print agent prompts for use with Claude Code
    print("\n" + "="*60)
    print("AGENT PROMPTS FOR CLAUDE CODE")
    print("="*60)

    for agent_name, agent_info in result["agents"].items():
        print(f"\n{'─'*60}")
        print(f"Agent: {agent_name.upper()}")
        print(f"{'─'*60}")
        print(agent_info["prompt"])

    print("\n" + "="*60)
    print(result["instructions"])
    print("="*60)


if __name__ == "__main__":
    main()
