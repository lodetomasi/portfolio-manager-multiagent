#!/usr/bin/env python3
"""
Portfolio Multi-Agent Analysis Runner

Main entry point for running the multi-agent portfolio analysis system.
Uses Claude Agent SDK to orchestrate specialized agents working in parallel.

Usage:
    python run_analysis.py                          # Interactive mode
    python run_analysis.py --portfolio my_portfolio.json
    python run_analysis.py --symbols SPY QQQ GLD --cash 10000
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator import MultiAgentOrchestrator


def load_portfolio_from_file(filepath: str) -> dict:
    """Load portfolio from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)


def create_portfolio_from_symbols(symbols: list, shares_per_symbol: int = 10, cash: float = 10000) -> dict:
    """Create portfolio from list of symbols"""
    holdings = []
    for symbol in symbols:
        holdings.append({
            "symbol": symbol.upper(),
            "shares": shares_per_symbol,
            "sector": "Unknown"  # Will be determined by market agent
        })

    return {
        "name": f"Portfolio with {', '.join(symbols)}",
        "holdings": holdings,
        "cash": cash
    }


async def interactive_mode():
    """Run in interactive mode - ask user for inputs"""
    print("\n" + "="*70)
    print("🤖 PORTFOLIO MULTI-AGENT ANALYSIS SYSTEM")
    print("="*70 + "\n")

    print("Enter your portfolio symbols (comma-separated, e.g., SPY,QQQ,GLD):")
    symbols_input = input("> ").strip()
    symbols = [s.strip().upper() for s in symbols_input.split(',')]

    print("\nEnter cash balance (default: 10000):")
    cash_input = input("> ").strip()
    cash = float(cash_input) if cash_input else 10000

    print("\nEnter shares per symbol (default: 50):")
    shares_input = input("> ").strip()
    shares = int(shares_input) if shares_input else 50

    portfolio = create_portfolio_from_symbols(symbols, shares, cash)

    print("\nSelect optimization objective:")
    print("  1. Maximize Sharpe Ratio (default)")
    print("  2. Minimize Variance")
    print("  3. Risk Parity")
    objective_input = input("> ").strip()

    objective_map = {
        "1": "max_sharpe",
        "2": "min_variance",
        "3": "risk_parity",
        "": "max_sharpe"
    }
    objective = objective_map.get(objective_input, "max_sharpe")

    return portfolio, objective


async def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Portfolio Analysis using Claude Agent SDK"
    )
    parser.add_argument(
        '--portfolio',
        type=str,
        help='Path to portfolio JSON file'
    )
    parser.add_argument(
        '--symbols',
        nargs='+',
        help='List of symbols (e.g., --symbols SPY QQQ GLD)'
    )
    parser.add_argument(
        '--cash',
        type=float,
        default=10000,
        help='Cash balance (default: 10000)'
    )
    parser.add_argument(
        '--shares',
        type=int,
        default=50,
        help='Shares per symbol (default: 50)'
    )
    parser.add_argument(
        '--objective',
        type=str,
        choices=['max_sharpe', 'min_variance', 'risk_parity'],
        default='max_sharpe',
        help='Optimization objective (default: max_sharpe)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for report (default: auto-generated)'
    )
    parser.add_argument(
        '--constraints',
        type=str,
        help='JSON file with optimization constraints'
    )

    args = parser.parse_args()

    # Determine portfolio source
    if args.portfolio:
        print(f"📂 Loading portfolio from {args.portfolio}...")
        portfolio = load_portfolio_from_file(args.portfolio)
        objective = args.objective
    elif args.symbols:
        print(f"📊 Creating portfolio from symbols: {', '.join(args.symbols)}")
        portfolio = create_portfolio_from_symbols(args.symbols, args.shares, args.cash)
        objective = args.objective
    else:
        # Interactive mode
        portfolio, objective = await interactive_mode()

    # Load constraints if provided
    constraints = None
    if args.constraints:
        with open(args.constraints, 'r') as f:
            constraints = json.load(f)

    # Display portfolio
    print(f"\n📋 Portfolio: {portfolio.get('name', 'Unnamed')}")
    print(f"   Holdings: {len(portfolio['holdings'])} positions")
    print(f"   Cash: ${portfolio.get('cash', 0):,.2f}")
    print(f"   Objective: {objective}\n")

    # Create orchestrator
    orchestrator = MultiAgentOrchestrator()

    # Run multi-agent analysis
    try:
        report = await orchestrator.run_full_analysis(
            portfolio=portfolio,
            optimization_objective=objective,
            constraints=constraints
        )

        # Display results
        print("\n" + "="*70)
        print("📊 ANALYSIS RESULTS")
        print("="*70 + "\n")

        # Summary
        summary = report.get('summary', {})

        print("KEY FINDINGS:")
        for finding in summary.get('key_findings', []):
            print(f"  • {finding}")

        print("\nRECOMMENDATIONS:")
        for rec in summary.get('recommendations', [])[:5]:
            print(f"  • {rec}")

        print("\nACTION ITEMS:")
        for action in summary.get('action_items', []):
            print(f"  ➤ {action}")

        # Save report
        output_file = args.output or f"portfolio_report_{orchestrator.session_id}.json"
        orchestrator.save_report(output_file)

        print(f"\n✅ Analysis complete!")
        print(f"📄 Full report saved to: {output_file}")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
