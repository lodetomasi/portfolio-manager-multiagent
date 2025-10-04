"""
Risk Analysis Utilities

Functions for portfolio risk assessment and stress testing.
"""

import statistics
from typing import List, Dict, Tuple
from datetime import datetime


class RiskAnalyzer:
    """Portfolio risk analysis tools"""

    @staticmethod
    def calculate_var(returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR) using historical simulation.

        Args:
            returns: List of historical returns
            confidence_level: Confidence level (default 95%)

        Returns:
            VaR as a positive number (loss)
        """
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))
        var = -sorted_returns[index] if index < len(sorted_returns) else 0

        return max(0, var)

    @staticmethod
    def calculate_cvar(returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR/Expected Shortfall).

        Args:
            returns: List of historical returns
            confidence_level: Confidence level (default 95%)

        Returns:
            CVaR as a positive number (expected loss beyond VaR)
        """
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))

        # Average of returns beyond VaR
        tail_returns = sorted_returns[:index] if index > 0 else [sorted_returns[0]]
        cvar = -statistics.mean(tail_returns) if tail_returns else 0

        return max(0, cvar)

    @staticmethod
    def calculate_correlation_matrix(returns_dict: Dict[str, List[float]]) -> Dict:
        """
        Calculate correlation matrix between assets.

        Args:
            returns_dict: Dictionary of {symbol: [returns]}

        Returns:
            Correlation matrix as nested dictionary
        """
        symbols = list(returns_dict.keys())
        n = len(symbols)

        if n == 0:
            return {}

        # Calculate correlation for each pair
        corr_matrix = {}
        for i, sym1 in enumerate(symbols):
            corr_matrix[sym1] = {}
            for j, sym2 in enumerate(symbols):
                if i == j:
                    corr_matrix[sym1][sym2] = 1.0
                else:
                    corr = RiskAnalyzer._calculate_correlation(
                        returns_dict[sym1],
                        returns_dict[sym2]
                    )
                    corr_matrix[sym1][sym2] = corr

        return corr_matrix

    @staticmethod
    def _calculate_correlation(x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n))

        denominator = (denominator_x * denominator_y) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator

    @staticmethod
    def stress_test_scenarios() -> List[Dict]:
        """
        Define stress test scenarios.

        Returns:
            List of stress test scenarios with expected impacts
        """
        return [
            {
                "name": "Market Crash (-20%)",
                "description": "Broad market decline of 20%",
                "impacts": {
                    "Equity": -0.20,
                    "Fixed Income": 0.05,
                    "Commodity": -0.10,
                    "Real Estate": -0.15
                }
            },
            {
                "name": "Inflation Spike",
                "description": "Inflation rises 3% above expectations",
                "impacts": {
                    "Equity": -0.08,
                    "Fixed Income": -0.15,
                    "Commodity": 0.12,
                    "Real Estate": 0.05
                }
            },
            {
                "name": "Interest Rate Shock",
                "description": "Fed raises rates 2% unexpectedly",
                "impacts": {
                    "Equity": -0.12,
                    "Fixed Income": -0.20,
                    "Commodity": -0.05,
                    "Real Estate": -0.18
                }
            },
            {
                "name": "Geopolitical Crisis",
                "description": "Major geopolitical event causing flight to safety",
                "impacts": {
                    "Equity": -0.15,
                    "Fixed Income": 0.08,
                    "Commodity": 0.10,
                    "Real Estate": -0.10
                }
            },
            {
                "name": "Tech Sector Crash",
                "description": "Technology sector declines 30%",
                "impacts": {
                    "Technology": -0.30,
                    "Broad Market": -0.12,
                    "Equity": -0.10,
                    "Fixed Income": 0.03,
                    "Commodity": -0.05
                }
            }
        ]

    @staticmethod
    def apply_stress_scenario(
        portfolio: Dict,
        scenario: Dict,
        current_values: Dict[str, float]
    ) -> Dict:
        """
        Apply stress scenario to portfolio.

        Args:
            portfolio: Portfolio holdings
            scenario: Stress scenario with impacts
            current_values: Current values of positions

        Returns:
            Stressed portfolio values and total impact
        """
        stressed_values = {}
        total_current = 0
        total_stressed = 0

        for holding in portfolio.get('holdings', []):
            symbol = holding['symbol']
            sector = holding.get('sector', 'Unknown')
            asset_class = holding.get('asset_class', 'Unknown')

            current_value = current_values.get(symbol, 0)
            total_current += current_value

            # Apply impact based on sector or asset class
            impact = scenario['impacts'].get(sector, scenario['impacts'].get(asset_class, 0))
            stressed_value = current_value * (1 + impact)
            total_stressed += stressed_value

            stressed_values[symbol] = {
                'current': current_value,
                'stressed': stressed_value,
                'impact': impact,
                'change': stressed_value - current_value
            }

        total_impact = (total_stressed - total_current) / total_current if total_current > 0 else 0

        return {
            'scenario': scenario['name'],
            'description': scenario['description'],
            'positions': stressed_values,
            'total_current_value': total_current,
            'total_stressed_value': total_stressed,
            'total_impact_pct': total_impact * 100,
            'total_impact_dollar': total_stressed - total_current
        }

    @staticmethod
    def calculate_concentration_risk(positions: List[Dict]) -> Dict:
        """
        Calculate concentration risk metrics.

        Args:
            positions: List of positions with weights

        Returns:
            Concentration risk metrics
        """
        if not positions:
            return {"herfindahl_index": 0, "max_position": 0, "top_3_concentration": 0}

        # Herfindahl-Hirschman Index (HHI)
        weights = [p.get('weight', 0) for p in positions]
        hhi = sum(w ** 2 for w in weights)

        # Max single position
        max_position = max(weights) if weights else 0

        # Top 3 concentration
        sorted_weights = sorted(weights, reverse=True)
        top_3 = sum(sorted_weights[:3])

        return {
            "herfindahl_index": hhi,
            "max_position_pct": max_position * 100,
            "top_3_concentration_pct": top_3 * 100,
            "effective_n_positions": 1 / hhi if hhi > 0 else 0,
            "concentration_level": RiskAnalyzer._assess_concentration_level(hhi)
        }

    @staticmethod
    def _assess_concentration_level(hhi: float) -> str:
        """Assess concentration level based on HHI"""
        if hhi > 0.25:
            return "High"
        elif hhi > 0.15:
            return "Moderate"
        else:
            return "Low"
