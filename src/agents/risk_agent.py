"""
Risk Assessment Agent - Uses Claude Agent SDK

This agent performs comprehensive risk analysis and stress testing.
"""

import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions
from typing import Dict
import json


class RiskAssessmentAgent:
    """Agent specialized in portfolio risk analysis"""

    def __init__(self):
        self.system_prompt = """You are a Portfolio Risk Management Agent.

Your mission: Identify, quantify, and assess portfolio risks comprehensively.

Core Responsibilities:
- Calculate Value at Risk (VaR) and Conditional VaR
- Conduct stress testing under various scenarios
- Analyze concentration and correlation risks
- Evaluate tail risk exposure
- Assess liquidity and market risks

Risk Categories:
1. Market Risk (beta, volatility, sensitivity)
2. Concentration Risk (HHI, top positions)
3. Sector/Geographic Exposure
4. Liquidity Risk
5. Correlation Breakdown Risk
6. Tail Risk (fat tails, extreme events)

Stress Test Scenarios:
- Market crash (-20%)
- Inflation spike (+3%)
- Interest rate shock (+2%)
- Geopolitical crisis
- Sector-specific crash

Output Format:
{
  "risk_metrics": {
    "var_95": float,
    "cvar_95": float,
    "beta": float,
    "volatility_annual": float
  },
  "concentration_risk": {
    "hhi": float,
    "max_position_pct": float,
    "top_3_pct": float,
    "level": "Low|Moderate|High"
  },
  "stress_tests": [
    {
      "scenario": str,
      "impact_pct": float,
      "impact_dollar": float,
      "description": str
    }
  ],
  "risk_scores": {
    "overall": int (1-10),
    "market": int,
    "concentration": int,
    "liquidity": int
  },
  "recommendations": [str]
}
"""

    async def assess(self, portfolio: Dict, market_data: Dict) -> Dict:
        """
        Perform comprehensive risk assessment.

        Args:
            portfolio: Portfolio holdings
            market_data: Current market data and volatility

        Returns:
            Risk assessment with metrics and recommendations
        """
        prompt = f"""Perform comprehensive risk assessment for this portfolio:

Portfolio:
{json.dumps(portfolio, indent=2)}

Market Data:
{json.dumps(market_data, indent=2)}

Risk Analysis Tasks:
1. Calculate VaR and CVaR at 95% confidence
2. Compute portfolio beta and volatility
3. Assess concentration risk using HHI
4. Run stress tests for 5 scenarios:
   - Market crash (-20%)
   - Inflation spike
   - Interest rate shock
   - Geopolitical crisis
   - Sector crash
5. Assign risk scores (1-10 scale) for different risk types
6. Provide specific risk mitigation recommendations

Use quantitative methods. Show calculations.
Return structured JSON matching the specified format.
"""

        options = ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            allowed_tools=["Bash", "WebSearch"]
        )

        print("[RiskAgent] Performing risk assessment...")
        result_text = ""
        async for message in query(prompt=prompt, options=options):
            # Skip SystemMessage metadata
            message_type = type(message).__name__
            if 'System' in message_type:
                print(f"[RiskAgent] Skipping {message_type}...")
                continue

            print(f"[RiskAgent] Processing {message_type}...")

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

        print(f"[RiskAgent] Parsing response ({len(result_text)} chars)...")

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
            print(f"[RiskAgent] JSON parsing failed: {e}")
            return {"error": "Failed to parse risk assessment", "raw": result_text[:500]}


async def main():
    """Example usage"""
    agent = RiskAssessmentAgent()

    portfolio = {
        "holdings": [
            {"symbol": "SPY", "shares": 100, "sector": "Broad Market"},
            {"symbol": "QQQ", "shares": 50, "sector": "Technology"},
            {"symbol": "GLD", "shares": 30, "sector": "Precious Metals"}
        ],
        "cash": 10000
    }

    market_data = {
        "SPY": {"price": 450.00, "volatility": 0.15},
        "QQQ": {"price": 380.00, "volatility": 0.22},
        "GLD": {"price": 190.00, "volatility": 0.18}
    }

    print("⚠️  Assessing portfolio risks...")
    print("=" * 60)

    assessment = await agent.assess(portfolio, market_data)
    print(json.dumps(assessment, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
