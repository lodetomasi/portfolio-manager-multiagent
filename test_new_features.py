#!/usr/bin/env python3
"""
Test new Claude Agent SDK features:
1. Custom Tools (real-time price fetching)
2. Safety Hooks (trade validation)
3. Background Tasks (Monte Carlo)
"""

import asyncio
import json
from src.tools.custom_tools import CustomPortfolioTools
from src.hooks.safety_hooks import PortfolioSafetyHooks
from src.tasks.background_tasks import BackgroundTaskManager


async def test_custom_tools():
    """Test custom tools for fast data fetching"""
    print("\n" + "="*70)
    print("TEST 1: Custom Tools - Real-Time Price Fetching")
    print("="*70)

    tools = CustomPortfolioTools()

    # Test 1: Fetch real-time prices
    print("\n📊 Fetching real-time prices for VWCE.DE, HYG, AGGH.MI...")
    prices = await tools.fetch_realtime_prices(['VWCE.DE', 'HYG', 'AGGH.MI'])

    for symbol, data in prices.items():
        if data.get('status') == 'success':
            print(f"  ✓ {symbol:12} ${data['price']:8.2f} ({data['change_pct']:+.2f}%)")
        else:
            print(f"  ✗ {symbol:12} {data.get('error', 'unknown error')}")

    # Test 2: Calculate portfolio metrics
    print("\n📈 Calculating portfolio metrics...")
    holdings = [
        {'symbol': 'VWCE.DE', 'shares': 46, 'price': prices['VWCE.DE']['price']},
        {'symbol': 'HYG', 'shares': 23, 'price': prices['HYG']['price']},
        {'symbol': 'AGGH.MI', 'shares': 150, 'price': prices['AGGH.MI']['price']}
    ]

    metrics = await tools.calculate_portfolio_metrics(holdings)
    print(f"  Total Value: ${metrics['total_value']:,.2f}")
    print(f"  HHI: {metrics['herfindahl_index']:.3f} ({metrics['concentration']})")
    print(f"  Effective N: {metrics['effective_n']:.2f}")

    print("\n  Position Weights:")
    for w in metrics['weights']:
        print(f"    {w['symbol']:12} {w['weight']*100:6.2f}%  (${w['value']:,.2f})")

    # Test 3: Check symbol availability
    print("\n🔍 Checking symbol availability...")
    symbols = ['VWCE.DE', 'INVALID.XX', 'SPY', 'NOTFOUND']
    availability = await tools.check_symbol_availability(symbols)

    for symbol, available in availability.items():
        status = "✓ Available" if available else "✗ Not found"
        print(f"  {symbol:12} {status}")


async def test_safety_hooks():
    """Test safety hooks for trade validation"""
    print("\n" + "="*70)
    print("TEST 2: Safety Hooks - Trade Validation")
    print("="*70)

    hooks = PortfolioSafetyHooks(constraints={
        'max_position_size': 0.35,
        'max_loss_threshold': -0.10,
        'forbidden_symbols': ['TQQQ', 'SQQQ']
    })

    # Test 1: Valid BUY trade
    print("\n📝 Test valid BUY trade...")
    result = await hooks.pre_trade_hook({
        'symbol': 'VWCE.DE',
        'action': 'BUY',
        'shares': 10,
        'price': 141.66,
        'current_portfolio': {'total_value': 10000}
    })
    print(f"  Decision: {result['permissionDecision']}")
    print(f"  Reason: {result['reason']}")

    # Test 2: Oversized position (should DENY)
    print("\n❌ Test oversized position (should DENY)...")
    result = await hooks.pre_trade_hook({
        'symbol': 'SPY',
        'action': 'BUY',
        'shares': 50,
        'price': 500,  # $25,000 on $10k portfolio = 71%
        'current_portfolio': {'total_value': 10000}
    })
    print(f"  Decision: {result['permissionDecision']}")
    print(f"  Reason: {result['reason']}")

    # Test 3: Forbidden symbol (should DENY)
    print("\n🚫 Test forbidden symbol TQQQ (should DENY)...")
    result = await hooks.pre_trade_hook({
        'symbol': 'TQQQ',
        'action': 'BUY',
        'shares': 10,
        'price': 50,
        'current_portfolio': {'total_value': 10000}
    })
    print(f"  Decision: {result['permissionDecision']}")
    print(f"  Reason: {result['reason']}")

    # Test 4: Large loss SELL (should WARN)
    print("\n⚠️  Test selling at loss (should WARN)...")
    result = await hooks.pre_trade_hook({
        'symbol': 'DFEN',
        'action': 'SELL',
        'shares': 14,
        'price': 40,
        'average_cost': 50,  # -20% loss
        'current_portfolio': {'total_value': 10000}
    })
    print(f"  Decision: {result['permissionDecision']}")
    print(f"  Reason: {result['reason']}")

    # Test 5: Pre-optimization validation
    print("\n🎯 Test pre-optimization validation...")
    result = await hooks.pre_optimization_hook({
        'portfolio': {'total_value': 15000},
        'objective': 'max_sharpe'
    })
    print(f"  Decision: {result['permissionDecision']}")
    print(f"  Reason: {result['reason']}")


async def test_background_tasks():
    """Test background tasks for Monte Carlo"""
    print("\n" + "="*70)
    print("TEST 3: Background Tasks - Monte Carlo Simulation")
    print("="*70)

    manager = BackgroundTaskManager()

    # Generate sample historical returns (normal distribution)
    import random
    random.seed(42)
    historical_returns = [random.gauss(0.0005, 0.015) for _ in range(252)]  # 1 year daily

    # Start Monte Carlo in background
    print("\n🚀 Starting Monte Carlo simulation (1000 paths) in background...")
    task_id = await manager.run_monte_carlo_background(
        task_id='test_mc_1000',
        historical_returns=historical_returns,
        num_simulations=1000,  # Reduced for speed
        horizon_days=252
    )

    print(f"  Task ID: {task_id}")

    # Check status immediately
    status = manager.get_status(task_id)
    print(f"  Status: {status['status']}")

    # Wait for completion with progress updates
    print("\n⏳ Waiting for completion...")
    while True:
        status = manager.get_status(task_id)
        if status['status'] == 'completed':
            break
        elif status['status'] == 'failed':
            print(f"  ❌ Task failed: {status.get('error')}")
            return
        elif status['status'] == 'running':
            progress = status.get('progress', 0)
            print(f"  Progress: {progress*100:.0f}%", end='\r')

        await asyncio.sleep(0.5)

    # Get result
    result = manager.get_result(task_id)
    print("\n\n✅ Monte Carlo Complete!")
    print(f"  Mean Return: {result['mean_return']*100:+.2f}%")
    print(f"  Median Return: {result['median_return']*100:+.2f}%")
    print(f"  Std Dev: {result['std_return']*100:.2f}%")
    print(f"  VaR 95%: {result['var_95']*100:.2f}%")
    print(f"  Expected Shortfall: {result['expected_shortfall_95']*100:.2f}%")
    print(f"  Prob of Loss: {result['probability_loss']*100:.1f}%")

    # Test task listing
    print("\n📋 All tasks:")
    for tid, st in manager.list_tasks().items():
        print(f"  {tid}: {st['status']}")


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 TESTING NEW CLAUDE AGENT SDK FEATURES")
    print("="*70)

    try:
        # Test 1: Custom Tools
        await test_custom_tools()

        # Test 2: Safety Hooks
        await test_safety_hooks()

        # Test 3: Background Tasks
        await test_background_tasks()

        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
