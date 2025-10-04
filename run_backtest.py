#!/usr/bin/env python3
"""
Backtesting Runner

Runs comprehensive backtests to validate agent predictions and strategies.

Usage:
    python run_backtest.py --portfolio portfolio.json
    python run_backtest.py --sample --periods all
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backtesting import PortfolioBacktester, BacktestPeriod
from backtesting.performance import PerformanceCalculator
from utils.market_data import create_sample_portfolio


async def main():
    parser = argparse.ArgumentParser(
        description="Run backtests to validate portfolio strategies"
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
        '--periods',
        type=str,
        default='recent',
        choices=['all', 'recent', 'crisis', 'long-term'],
        help='Which test periods to run'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='backtest_results.json',
        help='Output file for results'
    )
    parser.add_argument(
        '--validate-predictions',
        type=str,
        help='Path to predictions JSON file to validate'
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
    print(f"BACKTESTING VALIDATION SYSTEM")
    print(f"{'='*70}\n")
    print(f"Portfolio: {portfolio.get('name', 'Unnamed')}")
    print(f"Holdings: {len(portfolio['holdings'])} positions")
    print(f"Cash: ${portfolio.get('cash', 0):,.2f}\n")

    # Create backtester
    backtester = PortfolioBacktester()

    # Select test periods
    all_periods = backtester.define_test_periods()

    if args.periods == 'recent':
        test_periods = [p for p in all_periods if '2023' in p.start_date or '2024' in p.start_date]
    elif args.periods == 'crisis':
        test_periods = [p for p in all_periods if 'COVID' in p.description or 'Bear' in p.description]
    elif args.periods == 'long-term':
        test_periods = [p for p in all_periods if '10-Year' in p.description or '5-Year' in p.description]
    else:  # all
        test_periods = all_periods

    print(f"Running {len(test_periods)} backtests...\n")

    # Run backtests
    results = []
    for period in test_periods:
        result = await backtester.run_backtest(portfolio, period)
        results.append(result)
        print(f"✓ Completed: {period.description}\n")

    # Generate report
    print("\n" + "="*70)
    print("BACKTEST RESULTS SUMMARY")
    print("="*70 + "\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. {result.period.description}")
        print(f"   Period: {result.period.start_date} to {result.period.end_date}")
        print(f"   Total Return: {result.total_return_pct:+.2f}%")
        print(f"   Annualized Return: {result.annualized_return_pct:+.2f}%")
        print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"   Max Drawdown: {result.max_drawdown_pct:.2f}%")
        print()

    # Compare strategies if multiple tests
    if len(results) > 1:
        print("\n" + "="*70)
        print("STRATEGY COMPARISON")
        print("="*70 + "\n")

        comparison = backtester.compare_strategies(results)

        print(f"Number of Tests: {comparison['num_strategies']}")
        print(f"\nBest Sharpe Ratio: {comparison['metrics']['sharpe_ratios']['best']:.2f}")
        print(f"Best Return: {comparison['metrics']['returns']['best']:.2f}%")
        print(f"Best Drawdown (min): {comparison['metrics']['max_drawdowns']['best']:.2f}%")

        print(f"\nOverall Winner: Test #{comparison['winner']['index'] + 1}")
        print(f"Reason: {comparison['winner']['reason']}")

    # Validate predictions if provided
    if args.validate_predictions:
        print("\n" + "="*70)
        print("PREDICTION VALIDATION")
        print("="*70 + "\n")

        with open(args.validate_predictions, 'r') as f:
            predictions = json.load(f)

        # Validate each backtest against predictions
        for i, result in enumerate(results):
            validation = backtester.validate_predictions(predictions, result)

            print(f"\nTest #{i+1}: {result.period.description}")
            print(f"Overall Quality Score: {validation['overall_quality_score']:.1f}/100")

            for metric_name, metric_val in validation['validations'].items():
                print(f"\n  {metric_name}:")
                print(f"    Predicted: {metric_val['predicted']}")
                print(f"    Actual: {metric_val['actual']}")
                print(f"    Grade: {metric_val['grade']:.1f}/100")

            print("\n  Recommendations:")
            for rec in validation['recommendations']:
                print(f"    • {rec}")

    # Save results
    backtester.save_results(args.output)

    print("\n" + "="*70)
    print(f"✅ Backtesting complete!")
    print(f"📄 Results saved to: {args.output}")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
