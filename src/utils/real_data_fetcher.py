"""
Real Market Data Fetcher using yfinance

Provides real historical data for portfolio analysis.
Ensures all calculations use actual market data, not estimates.
"""

import yfinance as yf
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio


class RealDataFetcher:
    """Fetch real market data using yfinance for accurate calculations"""

    @staticmethod
    async def get_current_prices(symbols: List[str]) -> Dict[str, Dict]:
        """
        Get current prices and basic info for symbols using real data.

        Args:
            symbols: List of ticker symbols

        Returns:
            Dict with symbol -> {price, change_pct, volume, etc.}
        """
        result = {}

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="5d")  # Last 5 days for change calc

                if len(hist) > 0:
                    current_price = float(hist['Close'].iloc[-1])

                    # Calculate change
                    if len(hist) > 1:
                        prev_price = float(hist['Close'].iloc[-2])
                        change_pct = ((current_price - prev_price) / prev_price) * 100
                    else:
                        change_pct = 0.0

                    result[symbol] = {
                        'price': current_price,
                        'change_pct': change_pct,
                        'volume': int(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0,
                        'market_cap': info.get('marketCap', 0),
                        'pe_ratio': info.get('trailingPE', 0),
                        '52w_high': info.get('fiftyTwoWeekHigh', 0),
                        '52w_low': info.get('fiftyTwoWeekLow', 0),
                        'data_source': 'yfinance (real)',
                        'timestamp': datetime.now().isoformat()
                    }

                    print(f"[RealData] ✓ {symbol}: ${current_price:.2f} ({change_pct:+.2f}%)")
                else:
                    print(f"[RealData] ⚠️  No data for {symbol}")

            except Exception as e:
                print(f"[RealData] ❌ Error fetching {symbol}: {e}")

        return result

    @staticmethod
    async def get_historical_returns(symbols: List[str], period: str = "1y") -> Dict[str, List[float]]:
        """
        Get historical daily returns for accurate Sharpe/volatility calculations.

        Args:
            symbols: List of ticker symbols
            period: Period (1mo, 3mo, 6mo, 1y, 2y, 5y)

        Returns:
            Dict with symbol -> list of daily returns
        """
        result = {}

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)

                if len(hist) > 1:
                    # Calculate daily returns
                    prices = hist['Close'].values
                    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                    result[symbol] = returns
                    print(f"[RealData] ✓ {symbol}: {len(returns)} daily returns from real data")
                else:
                    result[symbol] = []
                    print(f"[RealData] ⚠️  Insufficient data for {symbol}")

            except Exception as e:
                print(f"[RealData] ❌ Error fetching returns for {symbol}: {e}")
                result[symbol] = []

        return result

    @staticmethod
    async def get_portfolio_historical_values(
        holdings: List[Dict],
        period: str = "1y"
    ) -> Dict:
        """
        Calculate portfolio values over time using real historical prices.

        Args:
            holdings: List of {symbol, shares} dicts
            period: Time period

        Returns:
            Dict with dates, values, returns
        """
        # Get symbols
        symbols = [h['symbol'] for h in holdings]

        # Fetch historical data
        all_hist = {}
        common_dates = None

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)

                if len(hist) > 0:
                    all_hist[symbol] = hist

                    # Find common dates
                    dates = set(hist.index.strftime('%Y-%m-%d'))
                    if common_dates is None:
                        common_dates = dates
                    else:
                        common_dates = common_dates.intersection(dates)

            except Exception as e:
                print(f"[RealData] ❌ Error fetching history for {symbol}: {e}")

        if not common_dates:
            print("[RealData] ⚠️  No common dates found")
            return {'dates': [], 'values': [], 'returns': []}

        # Sort dates
        sorted_dates = sorted(list(common_dates))

        # Calculate portfolio value for each date
        portfolio_values = []

        for date_str in sorted_dates:
            total_value = 0

            for holding in holdings:
                symbol = holding['symbol']
                shares = holding['shares']

                if symbol in all_hist:
                    hist = all_hist[symbol]
                    date_prices = hist[hist.index.strftime('%Y-%m-%d') == date_str]

                    if len(date_prices) > 0:
                        price = float(date_prices['Close'].iloc[0])
                        total_value += shares * price

            portfolio_values.append(total_value)

        # Calculate returns
        returns = []
        if len(portfolio_values) > 1:
            returns = [
                (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
                for i in range(1, len(portfolio_values))
            ]

        print(f"[RealData] ✓ Portfolio: {len(portfolio_values)} historical values calculated from real data")

        return {
            'dates': sorted_dates,
            'values': portfolio_values,
            'returns': returns,
            'data_source': 'yfinance (real historical)'
        }

    @staticmethod
    def calculate_real_metrics(returns: List[float], values: List[float]) -> Dict:
        """
        Calculate portfolio metrics from real historical data.

        Args:
            returns: Daily returns (real)
            values: Portfolio values (real)

        Returns:
            Dict with Sharpe, volatility, max drawdown, etc.
        """
        import statistics

        if not returns or not values:
            return {
                'sharpe_ratio': 0.0,
                'volatility': 0.0,
                'max_drawdown': 0.0,
                'total_return': 0.0,
                'data_quality': 'insufficient'
            }

        # Sharpe ratio
        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0

        risk_free_rate = 0.04
        excess_return = (avg_return * 252) - risk_free_rate
        annualized_vol = std_return * (252 ** 0.5)

        sharpe = excess_return / annualized_vol if annualized_vol > 0 else 0.0

        # Max drawdown
        peak = values[0]
        max_dd = 0.0

        for value in values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd

        # Total return
        total_return = (values[-1] - values[0]) / values[0] if values[0] > 0 else 0.0

        return {
            'sharpe_ratio': sharpe,
            'volatility': annualized_vol,
            'max_drawdown': max_dd,
            'total_return': total_return,
            'avg_daily_return': avg_return,
            'num_data_points': len(returns),
            'data_quality': 'real (yfinance)',
            'data_period': f"{len(returns)} days"
        }
