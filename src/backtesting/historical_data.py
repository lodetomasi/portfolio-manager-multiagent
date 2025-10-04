"""
Historical Data Retrieval for Backtesting

Fetches real historical price data for accurate backtesting.
Uses web search to gather historical ETF prices since we don't have API access.
"""

from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import asyncio


class HistoricalDataFetcher:
    """
    Fetches historical price data for backtesting.

    In production, this would integrate with:
    - Yahoo Finance API
    - Alpha Vantage
    - IEX Cloud
    - Polygon.io

    For this implementation, we'll use Claude Code's web search
    to gather historical data from financial websites.
    """

    def __init__(self):
        self.cache = {}

    async def fetch_historical_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        frequency: str = "daily"
    ) -> Dict:
        """
        Fetch historical prices for a symbol.

        Args:
            symbol: Stock/ETF ticker
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            frequency: 'daily', 'weekly', 'monthly'

        Returns:
            Dictionary with dates and prices
        """
        cache_key = f"{symbol}_{start_date}_{end_date}_{frequency}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        print(f"[HistoricalData] Fetching {symbol} from {start_date} to {end_date}...")

        # In real implementation, would query via Claude's WebSearch
        # For now, structure what we need:
        data = {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "frequency": frequency,
            "prices": [],  # List of {date, open, high, low, close, volume}
            "metadata": {
                "source": "Historical Database",
                "fetched_at": datetime.now().isoformat()
            }
        }

        # TODO: Implement actual web search query like:
        # query = f"{symbol} historical stock prices {start_date} to {end_date} daily data"
        # Use WebSearch tool to find data from Yahoo Finance, etc.
        # Parse the results into structured format

        self.cache[cache_key] = data
        return data

    async def fetch_multiple_symbols(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, Dict]:
        """
        Fetch historical data for multiple symbols in parallel.

        This is critical for backtesting portfolios.
        """
        print(f"[HistoricalData] Fetching {len(symbols)} symbols in parallel...")

        tasks = [
            self.fetch_historical_prices(symbol, start_date, end_date)
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks)

        return {
            symbols[i]: results[i]
            for i in range(len(symbols))
        }

    def calculate_returns(self, prices: List[Dict]) -> List[float]:
        """
        Calculate daily returns from price series.

        Args:
            prices: List of {date, close} dictionaries

        Returns:
            List of daily returns (fractional)
        """
        if len(prices) < 2:
            return []

        returns = []
        for i in range(1, len(prices)):
            prev_price = prices[i-1]['close']
            curr_price = prices[i]['close']
            daily_return = (curr_price - prev_price) / prev_price
            returns.append(daily_return)

        return returns

    def calculate_portfolio_values(
        self,
        holdings: List[Dict],
        historical_prices: Dict[str, Dict],
        start_date: str,
        end_date: str
    ) -> List[Dict]:
        """
        Calculate daily portfolio values over time.

        Critical for accurate backtesting.

        Args:
            holdings: List of {symbol, shares}
            historical_prices: Dict of symbol -> price data
            start_date, end_date: Period

        Returns:
            List of {date, total_value, holdings_value: {symbol: value}}
        """
        portfolio_values = []

        # Get all unique dates from price data
        all_dates = set()
        for symbol_data in historical_prices.values():
            for price_point in symbol_data.get('prices', []):
                all_dates.add(price_point['date'])

        sorted_dates = sorted(list(all_dates))

        for date in sorted_dates:
            if date < start_date or date > end_date:
                continue

            total_value = 0
            holdings_value = {}

            for holding in holdings:
                symbol = holding['symbol']
                shares = holding['shares']

                # Find price for this date
                symbol_prices = historical_prices.get(symbol, {}).get('prices', [])
                price_on_date = None

                for price_point in symbol_prices:
                    if price_point['date'] == date:
                        price_on_date = price_point['close']
                        break

                if price_on_date:
                    position_value = shares * price_on_date
                    total_value += position_value
                    holdings_value[symbol] = position_value

            portfolio_values.append({
                'date': date,
                'total_value': total_value,
                'holdings_value': holdings_value
            })

        return portfolio_values

    def get_price_on_date(
        self,
        symbol: str,
        date: str,
        historical_prices: Dict
    ) -> float:
        """Get closing price for a symbol on a specific date"""
        symbol_data = historical_prices.get(symbol, {})
        prices = symbol_data.get('prices', [])

        for price_point in prices:
            if price_point['date'] == date:
                return price_point['close']

        return None

    async def validate_data_quality(
        self,
        historical_data: Dict
    ) -> Dict:
        """
        Validate quality of historical data.

        Checks for:
        - Missing dates
        - Price anomalies
        - Data completeness
        - Suspicious gaps

        Returns validation report.
        """
        validation = {
            "symbol": historical_data['symbol'],
            "issues": [],
            "quality_score": 100,
            "recommendation": "OK"
        }

        prices = historical_data.get('prices', [])

        if not prices:
            validation["issues"].append("No price data available")
            validation["quality_score"] = 0
            validation["recommendation"] = "REJECT - No data"
            return validation

        # Check for missing dates
        dates = [p['date'] for p in prices]
        start = datetime.strptime(dates[0], "%Y-%m-%d")
        end = datetime.strptime(dates[-1], "%Y-%m-%d")
        expected_days = (end - start).days + 1
        actual_days = len(dates)

        missing_pct = ((expected_days - actual_days) / expected_days) * 100

        if missing_pct > 20:
            validation["issues"].append(f"Missing {missing_pct:.1f}% of expected dates")
            validation["quality_score"] -= 30

        # Check for price anomalies (sudden spikes/drops > 50%)
        for i in range(1, len(prices)):
            prev_price = prices[i-1]['close']
            curr_price = prices[i]['close']
            change = abs((curr_price - prev_price) / prev_price)

            if change > 0.50:  # 50% change in one day
                validation["issues"].append(
                    f"Suspicious price movement on {prices[i]['date']}: {change*100:.1f}%"
                )
                validation["quality_score"] -= 10

        # Final recommendation
        if validation["quality_score"] >= 90:
            validation["recommendation"] = "EXCELLENT - Use with confidence"
        elif validation["quality_score"] >= 75:
            validation["recommendation"] = "GOOD - Minor issues"
        elif validation["quality_score"] >= 60:
            validation["recommendation"] = "ACCEPTABLE - Review issues"
        else:
            validation["recommendation"] = "POOR - Do not use for critical analysis"

        return validation


class RealTimeDataAdapter:
    """
    Adapter to convert real-time market data into format compatible
    with historical backtesting.

    This allows testing strategies on live data as if it were historical.
    """

    def __init__(self):
        self.buffer = []

    def add_snapshot(self, date: str, prices: Dict[str, float]):
        """Add a market snapshot to the buffer"""
        self.buffer.append({
            "date": date,
            "prices": prices
        })

    def export_as_historical(self) -> Dict:
        """Convert buffered snapshots to historical data format"""
        if not self.buffer:
            return {}

        # Organize by symbol
        symbols = set()
        for snapshot in self.buffer:
            symbols.update(snapshot['prices'].keys())

        historical_data = {}

        for symbol in symbols:
            prices = []
            for snapshot in self.buffer:
                if symbol in snapshot['prices']:
                    prices.append({
                        'date': snapshot['date'],
                        'close': snapshot['prices'][symbol],
                        'open': snapshot['prices'][symbol],  # Simplified
                        'high': snapshot['prices'][symbol],
                        'low': snapshot['prices'][symbol],
                        'volume': 0  # Not available in real-time snapshots
                    })

            historical_data[symbol] = {
                'symbol': symbol,
                'start_date': self.buffer[0]['date'],
                'end_date': self.buffer[-1]['date'],
                'prices': prices,
                'metadata': {
                    'source': 'Real-time data buffer',
                    'num_snapshots': len(prices)
                }
            }

        return historical_data

    def clear_buffer(self):
        """Clear the snapshot buffer"""
        self.buffer = []
