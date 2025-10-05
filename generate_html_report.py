#!/usr/bin/env python3
"""
Generate User-Friendly HTML Report
Creates a beautiful visual report from portfolio analysis
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.html_report_generator import HTMLReportGenerator
from utils.real_data_fetcher import RealDataFetcher


async def generate_report(portfolio_path: str, output_path: str = None):
    """
    Generate HTML report from portfolio file.

    Args:
        portfolio_path: Path to portfolio JSON
        output_path: Optional output path for HTML (auto-generated if not provided)
    """
    # Load portfolio
    with open(portfolio_path, 'r') as f:
        portfolio = json.load(f)

    print(f"📊 Generating report for: {portfolio.get('name', 'Portfolio')}")
    print("="*60)

    # Fetch real data
    fetcher = RealDataFetcher()

    symbols = [h['symbol'] for h in portfolio['holdings']]
    print(f"\n🔍 Fetching real-time data for {len(symbols)} symbols...")

    # Get current prices
    prices = await fetcher.get_current_prices(symbols)

    # Get historical data
    print("📈 Fetching historical data (1 year)...")
    historical = await fetcher.get_portfolio_historical_values(
        portfolio['holdings'],
        period="1y"
    )

    # Calculate metrics
    print("📊 Calculating metrics...")
    if historical['returns'] and historical['values']:
        metrics = fetcher.calculate_real_metrics(
            historical['returns'],
            historical['values']
        )
    else:
        metrics = {}

    # Prepare data for report
    real_data = {
        'prices': prices,
        'sharpe_ratio': metrics.get('sharpe_ratio', 0),
        'volatility': metrics.get('volatility', 0),
        'max_drawdown': metrics.get('max_drawdown', 0),
        'total_return': metrics.get('total_return', 0),
        'avg_daily_return': metrics.get('avg_daily_return', 0),
        'num_data_points': metrics.get('num_data_points', 0),
        'data_period': metrics.get('data_period', '1 year'),
    }

    # Mock analysis results (in real system, these come from orchestrator)
    analysis_results = {
        'risk_score': 7,
        'recommendations': []
    }

    # Generate output path if not provided
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"portfolio_report_{timestamp}.html"

    # Generate HTML report
    print(f"\n✨ Generating HTML report...")
    html = HTMLReportGenerator.generate_report(
        portfolio=portfolio,
        analysis_results=analysis_results,
        real_data=real_data,
        output_path=output_path
    )

    print("\n" + "="*60)
    print(f"✅ Report generato con successo!")
    print(f"📄 File: {output_path}")
    print(f"🌐 Apri il file in un browser per visualizzare")
    print("="*60)

    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Generate user-friendly HTML report')
    parser.add_argument(
        '--portfolio',
        type=str,
        default='examples/my_portfolio_us_symbols.json',
        help='Path to portfolio JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output path for HTML file (optional)'
    )

    args = parser.parse_args()

    # Run async
    asyncio.run(generate_report(args.portfolio, args.output))
