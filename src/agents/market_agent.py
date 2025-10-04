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
        # Source reliability scoring (Anthropic pattern)
        self.source_reliability = {
            "bloomberg.com": 10,
            "reuters.com": 10,
            "ft.com": 9,
            "wsj.com": 9,
            "marketwatch.com": 8,
            "cnbc.com": 8,
            "investing.com": 7,
            "yahoo.com": 6,
            "seekingalpha.com": 6,
            "unknown": 3
        }

        self.system_prompt = """You are a Market Data Specialist Agent following Anthropic's multi-agent best practices.

PROGRESSIVE SEARCH STRATEGY:
1. Start BROAD: Query all symbols together first
2. Evaluate QUALITY: Check source reliability (Bloomberg, Reuters, official exchanges)
3. Narrow FOCUS: If incomplete, search specific symbols individually
4. Self-ADAPT: Adjust based on findings

RESOURCE ALLOCATION (Critical):
- Maximum 3-4 web searches total
- Stop when complete data obtained
- Each search should maximize information gain
- Prioritize reliable sources

AVOID DUPLICATE WORK:
- Track what data points you already have
- Don't re-query same information
- Combine multiple data from single source

Core Responsibilities:
- Search for current prices, volumes, market caps
- Find recent news and analyst ratings
- Extract financial ratios (P/E, dividend yield)
- Assess data quality and source reliability

Data Quality Standards:
- Cite sources with dates
- Prioritize last 24-48 hours
- Cross-reference when possible
- Flag uncertain data explicitly
- ALWAYS include source URL for each data point

Source Reliability Ranking (use in quality assessment):
- Tier 1 (score 9-10): Bloomberg, Reuters, FT, WSJ
- Tier 2 (score 7-8): MarketWatch, CNBC, Investing.com
- Tier 3 (score 5-6): Yahoo Finance, SeekingAlpha
- Unknown sources: score 3

Output Format (Extended):
{
  "symbols": {
    "TICKER": {
      "price": float,
      "change_pct": float,
      "volume": int,
      "market_cap": float,
      "pe_ratio": float,
      "52w_high": float,
      "52w_low": float,
      "news": [{"title": str, "date": str, "source": str, "url": str}],
      "analyst_rating": str,
      "data_quality": "excellent|good|limited",
      "sources": [{"url": str, "reliability_score": int (1-10)}]
    }
  },
  "meta": {
    "searches_performed": int,
    "strategy": "broad-first|targeted|mixed",
    "completion": "full|partial",
    "notes": "any important observations"
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
