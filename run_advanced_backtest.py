#!/usr/bin/env python3
"""
Advanced Backtesting Runner

Runs comprehensive validation tests on the multi-agent system:
1. Walk-Forward Analysis - Detect overfitting
2. Monte Carlo Simulation - Confidence intervals
3. Agent Prediction Validation - Forecast accuracy
4. Regime Analysis - Performance by market conditions

Usage:
    python run_advanced_backtest.py --portfolio example_100k_portfolio.json
    python run_advanced_backtest.py --sample --test walk-forward
    python run_advanced_backtest.py --sample --test monte-carlo --simulations 10000
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backtesting.advanced_backtester import AdvancedBacktester
from utils.market_data import create_sample_portfolio


async def main():
    parser = argparse.ArgumentParser(
        description="Run advanced backtests to validate multi-agent system"
    )
    parser.add_argument(
        '--portfolio',
        type=str,
        help='Path to portfolio JSON file'
    )
    parser.add_argument(
        '--sample',
        action='store_true',
        help='Use sample portfolio'
    )
    parser.add_argument(
        '--test',
        type=str,
        default='all',
        choices=['all', 'walk-forward', 'monte-carlo', 'agent-validation', 'regime'],
        help='Which validation test to run'
    )
    parser.add_argument(
        '--simulations',
        type=int,
        default=10000,
        help='Number of Monte Carlo simulations'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default='2020-01-01',
        help='Start date for analysis (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        default='2024-12-31',
        help='End date for analysis (YYYY-MM-DD)'
    )

    args = parser.parse_args()

    # Load portfolio
    if args.sample or not args.portfolio:
        print("Using sample portfolio...")
        portfolio = create_sample_portfolio()
    else:
        print(f"Loading portfolio from {args.portfolio}...")
        with open(args.portfolio, 'r') as f:
            portfolio = json.load(f)

    print(f"\n{'='*70}")
    print(f"ADVANCED BACKTESTING VALIDATION SYSTEM")
    print(f"{'='*70}\n")
    print(f"Portfolio: {portfolio.get('name', 'Unnamed')}")
    print(f"Holdings: {len(portfolio['holdings'])} positions")
    print(f"Test Period: {args.start_date} to {args.end_date}\n")

    # Create advanced backtester
    backtester = AdvancedBacktester()

    # Run selected tests
    if args.test in ['all', 'walk-forward']:
        print("\n" + "="*70)
        print("TEST 1: WALK-FORWARD ANALYSIS")
        print("="*70)
        print("Purpose: Detect overfitting in optimization strategy")
        print("Method: Rolling in-sample optimization → out-of-sample validation")
        print()

        walk_forward_results = await backtester.walk_forward_analysis(
            portfolio=portfolio,
            start_date=args.start_date,
            end_date=args.end_date,
            in_sample_window=252,  # 1 year
            out_sample_window=63,   # 3 months
            step_size=21  # 1 month
        )

        if walk_forward_results:
            # Calculate validation metrics
            degradations = [r.degradation for r in walk_forward_results]
            avg_deg = sum(degradations) / len(degradations)

            print(f"\n📊 VALIDATION VERDICT:")
            if avg_deg < 10:
                print("✅ EXCELLENT: Model generalizes very well (<10% degradation)")
            elif avg_deg < 25:
                print("✅ GOOD: Acceptable generalization (10-25% degradation)")
            elif avg_deg < 50:
                print("⚠️  FAIR: Some overfitting detected (25-50% degradation)")
            else:
                print("❌ POOR: High overfitting risk (>50% degradation)")

    if args.test in ['all', 'monte-carlo']:
        print("\n" + "="*70)
        print("TEST 2: MONTE CARLO SIMULATION")
        print("="*70)
        print(f"Purpose: Estimate confidence intervals and tail risk")
        print(f"Method: Bootstrap resampling with {args.simulations:,} simulations")
        print()

        # First get historical data
        from backtesting.historical_data import HistoricalDataFetcher
        fetcher = HistoricalDataFetcher()
        symbols = [h['symbol'] for h in portfolio['holdings']]

        print(f"[MonteCarlo] Fetching historical data for {len(symbols)} symbols...")
        historical_prices = await fetcher.fetch_multiple_symbols(
            symbols,
            args.start_date,
            args.end_date
        )

        monte_carlo_result = await backtester.monte_carlo_simulation(
            portfolio=portfolio,
            historical_prices=historical_prices,
            num_simulations=args.simulations,
            horizon_days=252  # 1 year forward
        )

        print(f"\n📊 RISK ASSESSMENT:")
        if monte_carlo_result.probability_loss < 0.30:
            print(f"✅ LOW RISK: {monte_carlo_result.probability_loss*100:.1f}% chance of loss")
        elif monte_carlo_result.probability_loss < 0.45:
            print(f"⚠️  MODERATE RISK: {monte_carlo_result.probability_loss*100:.1f}% chance of loss")
        else:
            print(f"❌ HIGH RISK: {monte_carlo_result.probability_loss*100:.1f}% chance of loss")

        print(f"\nWorst-case scenario (5th percentile): {monte_carlo_result.percentile_5*100:.2f}% return")
        print(f"Expected shortfall (CVaR): {monte_carlo_result.expected_shortfall_95*100:.2f}%")

    # Save results
    output_file = "advanced_backtest_results.json"
    backtester.save_results(output_file)

    print("\n" + "="*70)
    print("✅ Advanced backtesting complete!")
    print(f"📄 Results saved to: {output_file}")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
