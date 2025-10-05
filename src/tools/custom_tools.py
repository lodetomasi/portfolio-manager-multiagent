"""
Custom Tools for Claude Agent SDK
Provides fast, specialized functions for portfolio analysis.
"""

from typing import Dict, List
import yfinance as yf
from datetime import datetime
import asyncio


class CustomPortfolioTools:
    """Custom tools implemented as in-process MCP functions"""

    @staticmethod
    async def fetch_realtime_prices(symbols: List[str]) -> Dict[str, Dict]:
        """
        Fast real-time price fetcher using yfinance.

        Args:
            symbols: List of ticker symbols

        Returns:
            Dict with symbol -> {price, change_pct, volume, timestamp}
        """
        result = {}

        # Process symbols in parallel
        async def fetch_single(symbol: str):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")

                if len(hist) > 0:
                    current_price = float(hist['Close'].iloc[-1])

                    # Calculate change
                    if len(hist) > 1:
                        prev_price = float(hist['Close'].iloc[-2])
                        change_pct = ((current_price - prev_price) / prev_price) * 100
                    else:
                        change_pct = 0.0

                    return symbol, {
                        'price': current_price,
                        'change_pct': change_pct,
                        'volume': int(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0,
                        'timestamp': datetime.now().isoformat(),
                        'data_source': 'yfinance (real-time)',
                        'status': 'success'
                    }
                else:
                    return symbol, {
                        'status': 'no_data',
                        'error': 'No historical data available'
                    }

            except Exception as e:
                return symbol, {
                    'status': 'error',
                    'error': str(e)
                }

        # Fetch all symbols in parallel
        tasks = [fetch_single(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)

        # Build result dict
        for symbol, data in results:
            result[symbol] = data

        return result

    @staticmethod
    async def calculate_portfolio_metrics(holdings: List[Dict]) -> Dict:
        """
        Fast portfolio metrics calculation (MPT basics).

        Args:
            holdings: List of {symbol, shares, price} dicts

        Returns:
            Dict with total_value, weights, concentration metrics
        """
        total_value = sum(h['shares'] * h.get('price', 0) for h in holdings)

        if total_value == 0:
            return {
                'error': 'Portfolio value is zero',
                'total_value': 0
            }

        # Calculate weights
        weights = []
        for holding in holdings:
            position_value = holding['shares'] * holding.get('price', 0)
            weight = position_value / total_value
            weights.append({
                'symbol': holding['symbol'],
                'weight': weight,
                'value': position_value
            })

        # Herfindahl index (concentration)
        hhi = sum(w['weight'] ** 2 for w in weights)
        effective_n = 1 / hhi if hhi > 0 else 0

        # Concentration category
        if hhi < 0.15:
            concentration = 'Low'
        elif hhi < 0.25:
            concentration = 'Moderate'
        elif hhi < 0.35:
            concentration = 'Moderate-High'
        else:
            concentration = 'High'

        return {
            'total_value': total_value,
            'weights': weights,
            'herfindahl_index': hhi,
            'effective_n': effective_n,
            'concentration': concentration,
            'num_holdings': len(holdings),
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    async def check_symbol_availability(symbols: List[str]) -> Dict[str, bool]:
        """
        Quick check if symbols are available on Yahoo Finance.

        Args:
            symbols: List of ticker symbols

        Returns:
            Dict with symbol -> True/False availability
        """
        result = {}

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                result[symbol] = len(hist) > 0
            except:
                result[symbol] = False

        return result

    @staticmethod
    def validate_trade_constraints(
        trade: Dict,
        current_portfolio: Dict,
        constraints: Dict
    ) -> Dict:
        """
        Validate if a trade respects portfolio constraints.

        Args:
            trade: {symbol, action, shares, price}
            current_portfolio: Current portfolio dict
            constraints: {max_position_size, min_position_size, max_sector_exposure}

        Returns:
            Dict with valid: bool, reason: str
        """
        max_pos = constraints.get('max_position_size', 0.35)
        min_pos = constraints.get('min_position_size', 0.05)

        # Calculate new portfolio value
        current_value = current_portfolio.get('total_value', 0)
        trade_value = trade['shares'] * trade['price']

        if trade['action'] == 'BUY':
            new_value = current_value + trade_value
            position_weight = trade_value / new_value if new_value > 0 else 0

            if position_weight > max_pos:
                return {
                    'valid': False,
                    'reason': f'Position would exceed max size ({position_weight:.1%} > {max_pos:.1%})'
                }

        elif trade['action'] == 'SELL':
            # Check if selling into loss >10%
            avg_cost = trade.get('average_cost', trade['price'])
            loss_pct = (trade['price'] - avg_cost) / avg_cost if avg_cost > 0 else 0

            if loss_pct < -0.10:
                return {
                    'valid': False,
                    'reason': f'Selling at {loss_pct:.1%} loss (>10% threshold)',
                    'warning': True  # Not blocking, just warning
                }

        return {
            'valid': True,
            'reason': 'Trade respects all constraints'
        }
