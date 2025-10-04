"""
Market Data Utilities

Helper functions for collecting and processing market data.
These are utilities that agents can use, but the actual data collection
happens via Claude Code agents with web search capabilities.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class MarketDataProcessor:
    """Process and validate market data collected by agents"""

    @staticmethod
    def validate_price_data(data: Dict) -> bool:
        """Validate that price data has required fields"""
        required_fields = ['symbol', 'price', 'change', 'timestamp']
        return all(field in data for field in required_fields)

    @staticmethod
    def calculate_portfolio_value(holdings: List[Dict], prices: Dict) -> Dict:
        """Calculate total portfolio value from holdings and current prices"""
        total_value = 0
        positions = []

        for holding in holdings:
            symbol = holding['symbol']
            shares = holding['shares']

            if symbol in prices:
                current_price = prices[symbol]['price']
                position_value = shares * current_price
                total_value += position_value

                positions.append({
                    'symbol': symbol,
                    'shares': shares,
                    'price': current_price,
                    'value': position_value,
                    'weight': 0  # Will calculate after total is known
                })

        # Calculate weights
        for position in positions:
            position['weight'] = position['value'] / total_value if total_value > 0 else 0

        return {
            'total_value': total_value,
            'positions': positions,
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def format_agent_query(symbols: List[str]) -> str:
        """Format a web search query for market data"""
        symbol_str = ' OR '.join(symbols)
        today = datetime.now().strftime('%Y-%m-%d')
        return f"({symbol_str}) stock price {today} current market data"

    @staticmethod
    def parse_agent_response(response: str) -> Dict:
        """Parse JSON response from market data agent"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
                return json.loads(json_str)
            raise ValueError("Could not parse agent response as JSON")


class PortfolioMetrics:
    """Calculate portfolio performance metrics"""

    @staticmethod
    def calculate_returns(prices: List[float]) -> List[float]:
        """Calculate simple returns from price series"""
        if len(prices) < 2:
            return []
        return [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]

    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.04) -> float:
        """Calculate Sharpe ratio (annualized)"""
        if not returns:
            return 0.0

        import statistics
        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0

        if std_return == 0:
            return 0.0

        # Annualize assuming daily returns
        excess_return = (avg_return * 252) - risk_free_rate
        annualized_vol = std_return * (252 ** 0.5)

        return excess_return / annualized_vol

    @staticmethod
    def calculate_max_drawdown(values: List[float]) -> float:
        """Calculate maximum drawdown from portfolio values"""
        if not values:
            return 0.0

        peak = values[0]
        max_dd = 0.0

        for value in values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd

        return max_dd

    @staticmethod
    def calculate_volatility(returns: List[float], annualize: bool = True) -> float:
        """Calculate volatility (standard deviation of returns)"""
        if len(returns) < 2:
            return 0.0

        import statistics
        vol = statistics.stdev(returns)

        if annualize:
            vol *= (252 ** 0.5)  # Assuming daily returns

        return vol


def create_sample_portfolio() -> Dict:
    """Create a sample portfolio for testing"""
    return {
        "name": "Sample Diversified Portfolio",
        "holdings": [
            {
                "symbol": "SPY",
                "name": "SPDR S&P 500 ETF",
                "shares": 100,
                "sector": "Broad Market",
                "asset_class": "Equity"
            },
            {
                "symbol": "QQQ",
                "name": "Invesco QQQ Trust",
                "shares": 50,
                "sector": "Technology",
                "asset_class": "Equity"
            },
            {
                "symbol": "GLD",
                "name": "SPDR Gold Trust",
                "shares": 30,
                "sector": "Precious Metals",
                "asset_class": "Commodity"
            },
            {
                "symbol": "TLT",
                "name": "iShares 20+ Year Treasury Bond",
                "shares": 40,
                "sector": "Bonds",
                "asset_class": "Fixed Income"
            },
            {
                "symbol": "VNQ",
                "name": "Vanguard Real Estate ETF",
                "shares": 25,
                "sector": "Real Estate",
                "asset_class": "Real Estate"
            }
        ],
        "cash": 15000,
        "currency": "USD"
    }
