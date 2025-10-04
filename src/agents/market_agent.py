"""
Market Data Agent - Uses Claude Agent SDK

This agent collects real-time market data using Claude Code's web search capabilities.
"""

import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions
from typing import Dict, List
import json


class MarketDataAgent:
    """Agent specialized in collecting market data"""

    def __init__(self):
        self.system_prompt = """You are a Market Data Specialist Agent.

Your mission: Gather accurate, real-time financial market data.

Core Responsibilities:
- Search for current stock prices, volumes, and market caps
- Find recent news and analyst ratings
- Extract key financial ratios (P/E, P/B, dividend yield)
- Monitor market sentiment

Data Quality Standards:
- Always cite sources with dates
- Prioritize data from last 24-48 hours
- Cross-reference multiple sources
- Flag any stale or uncertain data

Output Format:
Return structured JSON with this format:
{
  "symbol": {
    "price": float,
    "change": float,
    "change_pct": float,
    "volume": int,
    "market_cap": float,
    "pe_ratio": float,
    "52w_high": float,
    "52w_low": float,
    "news": [{"title": str, "date": str, "source": str}],
    "analyst_rating": str,
    "price_target": float,
    "last_updated": str
  }
}
"""

    async def collect_data(self, symbols: List[str]) -> Dict:
        """
        Collect market data for given symbols using Claude Code web search.

        Args:
            symbols: List of ticker symbols (e.g., ['SPY', 'QQQ', 'GLD'])

        Returns:
            Dictionary with market data for each symbol
        """
        prompt = f"""Collect current market data for these symbols: {', '.join(symbols)}

For each symbol, search the web and gather:
1. Current price and daily change (%, $)
2. Trading volume and market cap
3. 52-week high/low
4. P/E ratio and key ratios
5. Latest news (last 7 days) - max 3 headlines with dates
6. Analyst consensus rating and price target

IMPORTANT STOP CONDITIONS:
- Do ONE web search per symbol to get current data
- DO NOT continue searching after you have basic data for all symbols
- IMMEDIATELY return JSON once you have prices and basic info
- DO NOT overthink or search for additional context
- Maximum 2-3 searches total

Use web search efficiently. Cite sources.
Return ONLY valid JSON matching the specified format and STOP.
"""

        options = ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            allowed_tools=["WebSearch", "WebFetch"]
        )

        print(f"[MarketDataAgent] Querying Claude for {len(symbols)} symbols...")
        result_text = ""

        try:
            # Add timeout to prevent infinite searching
            async with asyncio.timeout(120):  # 2 minute max
                async for message in query(prompt=prompt, options=options):
                    # Skip SystemMessage metadata
                    message_type = type(message).__name__
                    if 'System' in message_type:
                        print(f"[MarketDataAgent] Skipping {message_type}...")
                        continue

                    print(f"[MarketDataAgent] Processing {message_type}...")

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
        except asyncio.TimeoutError:
            print(f"[MarketDataAgent] WARNING: Query timed out after 120s")
            return {
                "error": "Market data collection timed out",
                "partial_data": result_text[:500] if result_text else "",
                "symbols_requested": symbols
            }

        print(f"[MarketDataAgent] Parsing response ({len(result_text)} chars)...")

        # Parse JSON from response
        try:
            # Extract JSON from potential markdown code blocks
            if "```json" in result_text:
                start = result_text.find("```json") + 7
                end = result_text.find("```", start)
                json_str = result_text[start:end].strip()
                return json.loads(json_str)
            else:
                # Try to parse directly
                return json.loads(result_text)
        except json.JSONDecodeError as e:
            print(f"[MarketDataAgent] JSON parsing failed: {e}")
            # Return structured data even if JSON parsing fails
            return {
                "error": "Failed to parse market data",
                "raw": result_text[:500],
                "symbols_requested": symbols
            }


async def main():
    """Example usage"""
    agent = MarketDataAgent()
    symbols = ["SPY", "QQQ", "GLD"]

    print(f"🔍 Collecting market data for: {', '.join(symbols)}")
    print("=" * 60)

    data = await agent.collect_data(symbols)
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
