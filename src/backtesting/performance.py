"""
Portfolio Performance Calculator

Calculates comprehensive performance metrics for backtesting validation.
All metrics use industry-standard formulas for accuracy.
"""

import statistics
from typing import List, Dict, Tuple
from datetime import datetime
import math


class PerformanceCalculator:
    """
    Calculate portfolio performance metrics with mathematical rigor.

    All calculations follow CFA Institute standards and
    Modern Portfolio Theory principles.
    """

    @staticmethod
    def calculate_returns(values: List[float]) -> List[float]:
        """
        Calculate period-to-period returns.

        Args:
            values: Time series of portfolio values

        Returns:
            List of returns (fractional, not percentage)
        """
        if len(values) < 2:
            return []

        returns = []
        for i in range(1, len(values)):
            ret = (values[i] - values[i-1]) / values[i-1]
            returns.append(ret)

        return returns

    @staticmethod
    def total_return(initial_value: float, final_value: float) -> float:
        """Calculate total return over period"""
        return (final_value - initial_value) / initial_value

    @staticmethod
    def annualized_return(
        initial_value: float,
        final_value: float,
        num_years: float
    ) -> float:
        """
        Calculate annualized return using geometric mean.

        Formula: (Final/Initial)^(1/years) - 1
        """
        if num_years <= 0 or initial_value <= 0:
            return 0.0

        return (final_value / initial_value) ** (1 / num_years) - 1

    @staticmethod
    def cagr(
        initial_value: float,
        final_value: float,
        num_years: float
    ) -> float:
        """
        Compound Annual Growth Rate.

        Same as annualized_return but more explicit naming.
        """
        return PerformanceCalculator.annualized_return(
            initial_value, final_value, num_years
        )

    @staticmethod
    def volatility(
        returns: List[float],
        annualize: bool = True,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate volatility (standard deviation of returns).

        Args:
            returns: List of period returns
            annualize: Whether to annualize the result
            periods_per_year: 252 for daily, 52 for weekly, 12 for monthly

        Returns:
            Volatility (annualized if requested)
        """
        if len(returns) < 2:
            return 0.0

        vol = statistics.stdev(returns)

        if annualize:
            vol *= math.sqrt(periods_per_year)

        return vol

    @staticmethod
    def sharpe_ratio(
        returns: List[float],
        risk_free_rate: float = 0.04,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sharpe Ratio.

        Formula: (Mean Return - Risk Free Rate) / Standard Deviation

        Args:
            returns: Period returns
            risk_free_rate: Annual risk-free rate (default 4%)
            periods_per_year: For annualization

        Returns:
            Sharpe ratio (annualized)
        """
        if len(returns) < 2:
            return 0.0

        mean_return = statistics.mean(returns)
        std_dev = statistics.stdev(returns)

        if std_dev == 0:
            return 0.0

        # Annualize
        annual_return = mean_return * periods_per_year
        annual_std = std_dev * math.sqrt(periods_per_year)

        sharpe = (annual_return - risk_free_rate) / annual_std

        return sharpe

    @staticmethod
    def sortino_ratio(
        returns: List[float],
        risk_free_rate: float = 0.04,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sortino Ratio (uses downside deviation instead of total volatility).

        Only penalizes downside volatility, not upside.
        """
        if len(returns) < 2:
            return 0.0

        mean_return = statistics.mean(returns)

        # Calculate downside deviation (only negative returns)
        downside_returns = [r for r in returns if r < 0]

        if not downside_returns:
            # No downside = infinite Sortino, cap at very high value
            return 10.0

        downside_dev = math.sqrt(sum(r**2 for r in downside_returns) / len(returns))

        if downside_dev == 0:
            return 10.0

        # Annualize
        annual_return = mean_return * periods_per_year
        annual_downside_dev = downside_dev * math.sqrt(periods_per_year)

        sortino = (annual_return - risk_free_rate) / annual_downside_dev

        return sortino

    @staticmethod
    def max_drawdown(values: List[float]) -> Tuple[float, int, int]:
        """
        Calculate maximum drawdown.

        Returns:
            (max_drawdown_pct, peak_index, trough_index)
        """
        if not values or len(values) < 2:
            return (0.0, 0, 0)

        peak = values[0]
        peak_idx = 0
        max_dd = 0.0
        max_dd_peak_idx = 0
        max_dd_trough_idx = 0

        for i, value in enumerate(values):
            if value > peak:
                peak = value
                peak_idx = i

            drawdown = (peak - value) / peak

            if drawdown > max_dd:
                max_dd = drawdown
                max_dd_peak_idx = peak_idx
                max_dd_trough_idx = i

        return (max_dd, max_dd_peak_idx, max_dd_trough_idx)

    @staticmethod
    def calmar_ratio(
        annualized_return: float,
        max_drawdown_pct: float
    ) -> float:
        """
        Calculate Calmar Ratio.

        Formula: Annualized Return / Max Drawdown

        Measures return per unit of maximum drawdown risk.
        """
        if max_drawdown_pct == 0:
            return 0.0

        return annualized_return / max_drawdown_pct

    @staticmethod
    def value_at_risk(
        returns: List[float],
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk using historical simulation.

        Args:
            returns: Historical returns
            confidence_level: e.g., 0.95 for 95% VaR

        Returns:
            VaR (as positive number representing potential loss)
        """
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))

        if index >= len(sorted_returns):
            index = len(sorted_returns) - 1

        var = -sorted_returns[index]  # Make positive (loss)

        return max(0, var)

    @staticmethod
    def conditional_var(
        returns: List[float],
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).

        Average loss beyond VaR threshold.
        """
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))

        if index == 0:
            index = 1

        # Average of worst returns beyond VaR
        tail_returns = sorted_returns[:index]

        if not tail_returns:
            return 0.0

        cvar = -statistics.mean(tail_returns)  # Make positive

        return max(0, cvar)

    @staticmethod
    def win_rate(returns: List[float]) -> float:
        """
        Calculate percentage of winning periods.

        Returns:
            Win rate as decimal (0.0 to 1.0)
        """
        if not returns:
            return 0.0

        winning_periods = sum(1 for r in returns if r > 0)
        total_periods = len(returns)

        return winning_periods / total_periods

    @staticmethod
    def profit_factor(returns: List[float]) -> float:
        """
        Calculate profit factor.

        Formula: Sum of Gains / Sum of Losses

        > 1.0 means profitable overall
        """
        if not returns:
            return 0.0

        gains = sum(r for r in returns if r > 0)
        losses = abs(sum(r for r in returns if r < 0))

        if losses == 0:
            return float('inf') if gains > 0 else 0.0

        return gains / losses

    @staticmethod
    def beta(
        portfolio_returns: List[float],
        benchmark_returns: List[float]
    ) -> float:
        """
        Calculate portfolio beta vs benchmark.

        Beta = Covariance(Portfolio, Benchmark) / Variance(Benchmark)
        """
        if len(portfolio_returns) != len(benchmark_returns):
            raise ValueError("Return series must be same length")

        if len(portfolio_returns) < 2:
            return 1.0

        # Calculate means
        port_mean = statistics.mean(portfolio_returns)
        bench_mean = statistics.mean(benchmark_returns)

        # Calculate covariance
        n = len(portfolio_returns)
        covariance = sum(
            (portfolio_returns[i] - port_mean) * (benchmark_returns[i] - bench_mean)
            for i in range(n)
        ) / (n - 1)

        # Calculate benchmark variance
        bench_variance = statistics.variance(benchmark_returns)

        if bench_variance == 0:
            return 1.0

        beta = covariance / bench_variance

        return beta

    @staticmethod
    def alpha(
        portfolio_return: float,
        benchmark_return: float,
        beta: float,
        risk_free_rate: float = 0.04
    ) -> float:
        """
        Calculate Jensen's Alpha.

        Alpha = Portfolio Return - [Risk Free Rate + Beta * (Benchmark Return - Risk Free Rate)]
        """
        expected_return = risk_free_rate + beta * (benchmark_return - risk_free_rate)
        alpha = portfolio_return - expected_return

        return alpha

    @staticmethod
    def information_ratio(
        portfolio_returns: List[float],
        benchmark_returns: List[float]
    ) -> float:
        """
        Calculate Information Ratio.

        IR = (Portfolio Return - Benchmark Return) / Tracking Error

        Measures risk-adjusted excess return vs benchmark.
        """
        if len(portfolio_returns) != len(benchmark_returns):
            raise ValueError("Return series must be same length")

        if len(portfolio_returns) < 2:
            return 0.0

        # Calculate excess returns
        excess_returns = [
            portfolio_returns[i] - benchmark_returns[i]
            for i in range(len(portfolio_returns))
        ]

        mean_excess = statistics.mean(excess_returns)
        tracking_error = statistics.stdev(excess_returns)

        if tracking_error == 0:
            return 0.0

        return mean_excess / tracking_error

    @staticmethod
    def ulcer_index(values: List[float]) -> float:
        """
        Calculate Ulcer Index (measure of downside volatility).

        Lower is better. Focuses on depth and duration of drawdowns.
        """
        if not values or len(values) < 2:
            return 0.0

        squared_drawdowns = []
        peak = values[0]

        for value in values:
            if value > peak:
                peak = value

            drawdown_pct = ((peak - value) / peak) * 100
            squared_drawdowns.append(drawdown_pct ** 2)

        ulcer = math.sqrt(sum(squared_drawdowns) / len(squared_drawdowns))

        return ulcer

    @staticmethod
    def comprehensive_metrics(
        values: List[float],
        benchmark_values: List[float] = None,
        risk_free_rate: float = 0.04,
        periods_per_year: int = 252
    ) -> Dict:
        """
        Calculate all performance metrics in one go.

        Returns comprehensive dictionary of metrics.
        """
        if not values or len(values) < 2:
            return {"error": "Insufficient data"}

        returns = PerformanceCalculator.calculate_returns(values)

        # Calculate time period
        num_periods = len(returns)
        num_years = num_periods / periods_per_year

        # Basic metrics
        total_ret = PerformanceCalculator.total_return(values[0], values[-1])
        annual_ret = PerformanceCalculator.annualized_return(values[0], values[-1], num_years)
        vol = PerformanceCalculator.volatility(returns, annualize=True, periods_per_year=periods_per_year)

        # Risk-adjusted metrics
        sharpe = PerformanceCalculator.sharpe_ratio(returns, risk_free_rate, periods_per_year)
        sortino = PerformanceCalculator.sortino_ratio(returns, risk_free_rate, periods_per_year)

        # Drawdown metrics
        max_dd, peak_idx, trough_idx = PerformanceCalculator.max_drawdown(values)
        calmar = PerformanceCalculator.calmar_ratio(annual_ret, max_dd)

        # Risk metrics
        var_95 = PerformanceCalculator.value_at_risk(returns, 0.95)
        cvar_95 = PerformanceCalculator.conditional_var(returns, 0.95)

        # Win/loss metrics
        win_rate = PerformanceCalculator.win_rate(returns)
        profit_factor = PerformanceCalculator.profit_factor(returns)

        ulcer = PerformanceCalculator.ulcer_index(values)

        metrics = {
            "period": {
                "num_periods": num_periods,
                "num_years": round(num_years, 2),
                "start_value": values[0],
                "end_value": values[-1]
            },
            "returns": {
                "total_pct": round(total_ret * 100, 2),
                "annualized_pct": round(annual_ret * 100, 2),
                "volatility_annual_pct": round(vol * 100, 2)
            },
            "risk_adjusted": {
                "sharpe_ratio": round(sharpe, 2),
                "sortino_ratio": round(sortino, 2),
                "calmar_ratio": round(calmar, 2)
            },
            "drawdown": {
                "max_drawdown_pct": round(max_dd * 100, 2),
                "peak_index": peak_idx,
                "trough_index": trough_idx
            },
            "risk": {
                "var_95_pct": round(var_95 * 100, 2),
                "cvar_95_pct": round(cvar_95 * 100, 2),
                "ulcer_index": round(ulcer, 2)
            },
            "win_loss": {
                "win_rate_pct": round(win_rate * 100, 2),
                "profit_factor": round(profit_factor, 2)
            }
        }

        # Add benchmark comparison if provided
        if benchmark_values and len(benchmark_values) == len(values):
            bench_returns = PerformanceCalculator.calculate_returns(benchmark_values)
            bench_annual_ret = PerformanceCalculator.annualized_return(
                benchmark_values[0], benchmark_values[-1], num_years
            )

            beta = PerformanceCalculator.beta(returns, bench_returns)
            alpha = PerformanceCalculator.alpha(annual_ret, bench_annual_ret, beta, risk_free_rate)
            info_ratio = PerformanceCalculator.information_ratio(returns, bench_returns)

            metrics["vs_benchmark"] = {
                "beta": round(beta, 2),
                "alpha_pct": round(alpha * 100, 2),
                "information_ratio": round(info_ratio, 2),
                "excess_return_pct": round((annual_ret - bench_annual_ret) * 100, 2)
            }

        return metrics
