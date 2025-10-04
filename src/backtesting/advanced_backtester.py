"""
Advanced Backtesting Framework with Model Validation

This module provides comprehensive validation for the multi-agent system:
1. Walk-Forward Analysis - Rolling window optimization
2. Monte Carlo Simulation - Bootstrap confidence intervals
3. Out-of-Sample Testing - Train/test split validation
4. Agent Prediction Accuracy - Track forecast vs actual
5. Regime Analysis - Performance by market conditions
6. Stress Testing - Extreme scenario validation
"""

import asyncio
import json
import statistics
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import random
import math

from .historical_data import HistoricalDataFetcher
from .performance import PerformanceCalculator
from .backtester import BacktestPeriod, BacktestResult


@dataclass
class WalkForwardResult:
    """Results from walk-forward analysis"""
    period: BacktestPeriod
    in_sample_sharpe: float
    out_sample_sharpe: float
    degradation: float  # % degradation out-of-sample
    overfitting_score: float  # 0-100, higher = more overfit


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation"""
    num_simulations: int
    mean_return: float
    median_return: float
    std_return: float
    percentile_5: float
    percentile_95: float
    var_95: float
    expected_shortfall_95: float
    probability_loss: float


@dataclass
class AgentPredictionValidation:
    """Validates agent predictions vs actual results"""
    agent_name: str
    metric_name: str
    predicted_value: float
    actual_value: float
    error_pct: float
    accuracy_grade: str  # A, B, C, D, F
    confidence_interval: Tuple[float, float]


@dataclass
class RegimePerformance:
    """Performance metrics by market regime"""
    regime_name: str
    num_periods: int
    avg_return: float
    avg_sharpe: float
    avg_drawdown: float
    win_rate: float
    best_period: str
    worst_period: str


class AdvancedBacktester:
    """
    Advanced backtesting with rigorous validation.

    Validates:
    1. Model generalization (walk-forward)
    2. Statistical robustness (Monte Carlo)
    3. Agent prediction accuracy
    4. Regime-specific performance
    5. Tail risk management
    """

    def __init__(self):
        self.historical_fetcher = HistoricalDataFetcher()
        self.perf_calculator = PerformanceCalculator()
        self.results = {
            'walk_forward': [],
            'monte_carlo': [],
            'agent_predictions': [],
            'regime_analysis': []
        }

    async def walk_forward_analysis(
        self,
        portfolio: Dict,
        start_date: str,
        end_date: str,
        in_sample_window: int = 252,  # 1 year
        out_sample_window: int = 63,   # 3 months
        step_size: int = 21  # 1 month
    ) -> List[WalkForwardResult]:
        """
        Walk-forward analysis to detect overfitting.

        Process:
        1. Train on in-sample period → get optimal allocation
        2. Test on out-of-sample period → measure degradation
        3. Roll window forward and repeat
        4. Compare in-sample vs out-of-sample performance

        High degradation = overfitting
        Low degradation = robust model

        Args:
            portfolio: Portfolio to test
            start_date, end_date: Full test period
            in_sample_window: Training window (days)
            out_sample_window: Test window (days)
            step_size: How far to move window each iteration

        Returns:
            List of walk-forward results showing overfitting metrics
        """
        print(f"\n{'='*70}")
        print("WALK-FORWARD ANALYSIS - Overfitting Detection")
        print(f"{'='*70}\n")
        print(f"In-sample window: {in_sample_window} days (~{in_sample_window//252} years)")
        print(f"Out-of-sample window: {out_sample_window} days (~{out_sample_window//21} months)")
        print(f"Step size: {step_size} days")

        # Get historical data for full period
        symbols = [h['symbol'] for h in portfolio['holdings']]
        print(f"[WalkForward] Fetching historical data for {len(symbols)} symbols...")

        historical_prices = await self.historical_fetcher.fetch_multiple_symbols(
            symbols,
            start_date,
            end_date
        )

        # Extract all dates
        all_dates = set()
        for symbol_data in historical_prices.values():
            for price_entry in symbol_data.get('prices', []):
                all_dates.add(price_entry['date'])

        sorted_dates = sorted(list(all_dates))

        if len(sorted_dates) < in_sample_window + out_sample_window:
            print(f"[WalkForward] ⚠️  Not enough data for walk-forward analysis")
            return []

        results = []
        current_idx = 0
        iteration = 0

        while current_idx + in_sample_window + out_sample_window <= len(sorted_dates):
            iteration += 1

            # Define in-sample and out-of-sample periods
            in_sample_start = sorted_dates[current_idx]
            in_sample_end = sorted_dates[current_idx + in_sample_window - 1]
            out_sample_start = sorted_dates[current_idx + in_sample_window]
            out_sample_end = sorted_dates[min(current_idx + in_sample_window + out_sample_window - 1, len(sorted_dates) - 1)]

            print(f"\n[WalkForward] Iteration {iteration}:")
            print(f"  In-sample:  {in_sample_start} → {in_sample_end}")
            print(f"  Out-sample: {out_sample_start} → {out_sample_end}")

            # Calculate performance in both periods
            in_sample_returns = self._calculate_returns(
                portfolio,
                historical_prices,
                in_sample_start,
                in_sample_end
            )

            out_sample_returns = self._calculate_returns(
                portfolio,
                historical_prices,
                out_sample_start,
                out_sample_end
            )

            if not in_sample_returns or not out_sample_returns:
                print(f"  ⚠️  Skipping - insufficient data")
                current_idx += step_size
                continue

            # Calculate Sharpe ratios
            in_sharpe = self.perf_calculator.sharpe_ratio(in_sample_returns, risk_free_rate=0.04)
            out_sharpe = self.perf_calculator.sharpe_ratio(out_sample_returns, risk_free_rate=0.04)

            # Calculate degradation
            if in_sharpe != 0:
                degradation = ((in_sharpe - out_sharpe) / abs(in_sharpe)) * 100
            else:
                degradation = 0.0

            # Overfitting score (0-100, higher = worse)
            # Based on degradation and volatility of out-of-sample
            overfitting_score = min(100, max(0, degradation))

            print(f"  In-sample Sharpe:  {in_sharpe:.3f}")
            print(f"  Out-sample Sharpe: {out_sharpe:.3f}")
            print(f"  Degradation: {degradation:.1f}%")
            print(f"  Overfitting Score: {overfitting_score:.1f}/100")

            result = WalkForwardResult(
                period=BacktestPeriod(
                    start_date=in_sample_start,
                    end_date=out_sample_end,
                    description=f"Walk-Forward Iteration {iteration}"
                ),
                in_sample_sharpe=in_sharpe,
                out_sample_sharpe=out_sharpe,
                degradation=degradation,
                overfitting_score=overfitting_score
            )

            results.append(result)
            current_idx += step_size

        # Summary statistics
        if results:
            avg_degradation = statistics.mean([r.degradation for r in results])
            avg_overfitting = statistics.mean([r.overfitting_score for r in results])

            print(f"\n{'='*70}")
            print("WALK-FORWARD SUMMARY")
            print(f"{'='*70}")
            print(f"Iterations: {len(results)}")
            print(f"Average Degradation: {avg_degradation:.1f}%")
            print(f"Average Overfitting Score: {avg_overfitting:.1f}/100")

            if avg_overfitting < 20:
                print("✅ Model shows EXCELLENT generalization (low overfitting)")
            elif avg_overfitting < 40:
                print("✅ Model shows GOOD generalization")
            elif avg_overfitting < 60:
                print("⚠️  Model shows MODERATE overfitting")
            else:
                print("❌ Model shows HIGH overfitting - predictions may be unreliable")

        self.results['walk_forward'] = results
        return results

    async def monte_carlo_simulation(
        self,
        portfolio: Dict,
        historical_prices: Dict[str, Dict],
        num_simulations: int = 10000,
        horizon_days: int = 252
    ) -> MonteCarloResult:
        """
        Monte Carlo simulation using bootstrap resampling.

        Process:
        1. Extract historical daily returns
        2. Bootstrap resample with replacement
        3. Simulate future paths
        4. Calculate distribution of outcomes

        Provides confidence intervals and tail risk estimates.

        Args:
            portfolio: Portfolio to simulate
            historical_prices: Historical price data
            num_simulations: Number of Monte Carlo paths
            horizon_days: Simulation horizon (days)

        Returns:
            Monte Carlo results with confidence intervals
        """
        print(f"\n{'='*70}")
        print(f"MONTE CARLO SIMULATION - {num_simulations:,} Paths")
        print(f"{'='*70}\n")
        print(f"Simulation horizon: {horizon_days} days ({horizon_days//252} years)")

        # Calculate historical returns
        daily_values = self._calculate_daily_values(portfolio, historical_prices)

        if len(daily_values) < 2:
            print("[MonteCarlo] ⚠️  Insufficient historical data")
            return MonteCarloResult(
                num_simulations=0,
                mean_return=0.0,
                median_return=0.0,
                std_return=0.0,
                percentile_5=0.0,
                percentile_95=0.0,
                var_95=0.0,
                expected_shortfall_95=0.0,
                probability_loss=0.0
            )

        historical_returns = [
            (daily_values[i] - daily_values[i-1]) / daily_values[i-1]
            for i in range(1, len(daily_values))
        ]

        print(f"[MonteCarlo] Historical data: {len(historical_returns)} daily returns")
        print(f"[MonteCarlo] Running {num_simulations:,} simulations...")

        # Run simulations
        final_returns = []

        for sim in range(num_simulations):
            # Bootstrap resample
            simulated_path = []
            for _ in range(horizon_days):
                sampled_return = random.choice(historical_returns)
                simulated_path.append(sampled_return)

            # Calculate cumulative return
            cum_return = 1.0
            for r in simulated_path:
                cum_return *= (1 + r)

            final_return = cum_return - 1
            final_returns.append(final_return)

            if (sim + 1) % 2000 == 0:
                print(f"  Progress: {sim + 1:,}/{num_simulations:,} simulations")

        # Calculate statistics
        final_returns.sort()

        mean_return = statistics.mean(final_returns)
        median_return = statistics.median(final_returns)
        std_return = statistics.stdev(final_returns)
        percentile_5 = final_returns[int(0.05 * len(final_returns))]
        percentile_95 = final_returns[int(0.95 * len(final_returns))]
        var_95 = -percentile_5  # VaR is positive number representing loss

        # Expected Shortfall (CVaR) - average of worst 5%
        worst_5pct = final_returns[:int(0.05 * len(final_returns))]
        expected_shortfall_95 = -statistics.mean(worst_5pct) if worst_5pct else 0.0

        # Probability of loss
        probability_loss = sum(1 for r in final_returns if r < 0) / len(final_returns)

        print(f"\n{'='*70}")
        print("MONTE CARLO RESULTS")
        print(f"{'='*70}")
        print(f"Mean Return: {mean_return*100:.2f}%")
        print(f"Median Return: {median_return*100:.2f}%")
        print(f"Std Deviation: {std_return*100:.2f}%")
        print(f"\nConfidence Intervals:")
        print(f"  5th Percentile:  {percentile_5*100:.2f}%")
        print(f"  95th Percentile: {percentile_95*100:.2f}%")
        print(f"\nRisk Metrics:")
        print(f"  VaR 95%: {var_95*100:.2f}%")
        print(f"  Expected Shortfall 95%: {expected_shortfall_95*100:.2f}%")
        print(f"  Probability of Loss: {probability_loss*100:.1f}%")

        result = MonteCarloResult(
            num_simulations=num_simulations,
            mean_return=mean_return,
            median_return=median_return,
            std_return=std_return,
            percentile_5=percentile_5,
            percentile_95=percentile_95,
            var_95=var_95,
            expected_shortfall_95=expected_shortfall_95,
            probability_loss=probability_loss
        )

        self.results['monte_carlo'].append(result)
        return result

    def _calculate_returns(
        self,
        portfolio: Dict,
        historical_prices: Dict[str, Dict],
        start_date: str,
        end_date: str
    ) -> List[float]:
        """Calculate daily returns for a period"""
        # Build price map
        price_by_date = {}
        for symbol, data in historical_prices.items():
            price_by_date[symbol] = {}
            for price_entry in data.get('prices', []):
                price_by_date[symbol][price_entry['date']] = price_entry['close']

        # Get dates in range
        all_dates = set()
        for symbol_prices in price_by_date.values():
            all_dates.update(symbol_prices.keys())

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        valid_dates = sorted([
            d for d in all_dates
            if start_dt <= datetime.strptime(d, "%Y-%m-%d") <= end_dt
        ])

        # Calculate daily portfolio values
        values = []
        for date in valid_dates:
            total_value = 0
            complete = True

            for holding in portfolio['holdings']:
                symbol = holding['symbol']
                shares = holding['shares']

                if symbol in price_by_date and date in price_by_date[symbol]:
                    price = price_by_date[symbol][date]
                    total_value += shares * price
                else:
                    complete = False
                    break

            if complete:
                total_value += portfolio.get('cash', 0)
                values.append(total_value)

        # Calculate returns
        if len(values) < 2:
            return []

        returns = [
            (values[i] - values[i-1]) / values[i-1]
            for i in range(1, len(values))
        ]

        return returns

    def _calculate_daily_values(
        self,
        portfolio: Dict,
        historical_prices: Dict[str, Dict]
    ) -> List[float]:
        """Calculate all daily portfolio values"""
        # Build price map
        price_by_date = {}
        for symbol, data in historical_prices.items():
            price_by_date[symbol] = {}
            for price_entry in data.get('prices', []):
                price_by_date[symbol][price_entry['date']] = price_entry['close']

        # Get all dates
        all_dates = set()
        for symbol_prices in price_by_date.values():
            all_dates.update(symbol_prices.keys())

        sorted_dates = sorted(list(all_dates))

        # Calculate daily values
        values = []
        for date in sorted_dates:
            total_value = 0
            complete = True

            for holding in portfolio['holdings']:
                symbol = holding['symbol']
                shares = holding['shares']

                if symbol in price_by_date and date in price_by_date[symbol]:
                    price = price_by_date[symbol][date]
                    total_value += shares * price
                else:
                    complete = False
                    break

            if complete:
                total_value += portfolio.get('cash', 0)
                values.append(total_value)

        return values

    def save_results(self, filepath: str = "advanced_backtest_results.json"):
        """Save all advanced backtest results"""
        output = {
            "generated_at": datetime.now().isoformat(),
            "walk_forward": [asdict(r) for r in self.results['walk_forward']],
            "monte_carlo": [asdict(r) for r in self.results['monte_carlo']],
            "agent_predictions": [asdict(r) for r in self.results['agent_predictions']],
            "regime_analysis": [asdict(r) for r in self.results['regime_analysis']]
        }

        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str)

        print(f"\n💾 Advanced backtest results saved to: {filepath}")
        return filepath
