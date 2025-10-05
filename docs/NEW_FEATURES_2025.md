# New Features - Claude Agent SDK Integration (2025)

This document describes the new features added to the Portfolio Manager using the latest Claude Agent SDK capabilities.

## 🆕 Overview

Three major enhancements have been integrated:

1. **Custom Tools** - Fast, in-process functions for real-time data
2. **Safety Hooks** - Automated trade validation and risk controls
3. **Background Tasks** - Non-blocking Monte Carlo simulations

---

## 1. Custom Tools

### Purpose
Eliminate overhead of full agent invocations for simple, repetitive tasks like price fetching.

### Implementation
Located in `src/tools/custom_tools.py`

### Features

#### 1.1 Real-Time Price Fetcher
```python
from src.tools.custom_tools import CustomPortfolioTools

tools = CustomPortfolioTools()
prices = await tools.fetch_realtime_prices(['VWCE.DE', 'HYG', 'AGGH.MI'])
```

**Output:**
```json
{
  "VWCE.DE": {
    "price": 141.66,
    "change_pct": 0.43,
    "volume": 1234567,
    "timestamp": "2025-10-04T18:00:00",
    "data_source": "yfinance (real-time)",
    "status": "success"
  }
}
```

**Benefits:**
- **3x faster** than WebSearch agent
- Parallel fetching for multiple symbols
- Direct yfinance integration

#### 1.2 Portfolio Metrics Calculator
```python
metrics = await tools.calculate_portfolio_metrics(holdings)
```

**Returns:**
- Total portfolio value
- Position weights
- Herfindahl Index (concentration)
- Effective N (diversification)

#### 1.3 Symbol Availability Checker
```python
availability = await tools.check_symbol_availability(['SPY', 'INVALID.XX'])
# Returns: {'SPY': True, 'INVALID.XX': False}
```

### Performance
- **Price fetch:** 2-5s (vs 30-60s with MarketDataAgent)
- **Metrics calc:** <1s
- **Parallel processing:** Yes (asyncio)

---

## 2. Safety Hooks

### Purpose
Automated validation of trades and optimization to prevent dangerous operations.

### Implementation
Located in `src/hooks/safety_hooks.py`

### Hook Types

#### 2.1 Pre-Optimization Hook
Validates inputs before optimization runs.

**Checks:**
- Portfolio value minimum ($1,000)
- Valid optimization objective
- Constraint completeness

**Example:**
```python
hooks = PortfolioSafetyHooks()
result = await hooks.pre_optimization_hook({
    'portfolio': {'total_value': 500},  # Too small!
    'objective': 'max_sharpe'
})
# Returns: {'permissionDecision': 'deny', 'reason': 'Portfolio value too small'}
```

#### 2.2 Pre-Trade Hook
Validates individual trades before execution.

**Checks:**
1. **Forbidden symbols** (3X leveraged ETFs: TQQQ, SQQQ, etc.)
2. **Position size limits** (default: max 35%)
3. **Large loss detection** (>10% loss threshold)
4. **Leverage detection** (warns on 3X pattern in symbol)
5. **Invalid parameters** (zero shares/price)

**Example - Forbidden Symbol:**
```python
result = await hooks.pre_trade_hook({
    'symbol': 'TQQQ',
    'action': 'BUY',
    'shares': 10,
    'price': 50,
    'current_portfolio': {'total_value': 10000}
})
# Returns: {'permissionDecision': 'deny', 'reason': 'TQQQ is in forbidden list (high-risk leveraged instrument)'}
```

**Example - Oversized Position:**
```python
result = await hooks.pre_trade_hook({
    'symbol': 'SPY',
    'action': 'BUY',
    'shares': 50,
    'price': 500,  # $25,000 on $10k portfolio = 71%
    'current_portfolio': {'total_value': 10000}
})
# Returns: {'permissionDecision': 'deny', 'reason': 'Position size 71.4% exceeds max 35.0%'}
```

**Example - Large Loss Warning:**
```python
result = await hooks.pre_trade_hook({
    'symbol': 'DFEN',
    'action': 'SELL',
    'shares': 14,
    'price': 40,
    'average_cost': 50,  # -20% loss
    'current_portfolio': {'total_value': 10000}
})
# Returns: {'permissionDecision': 'warn', 'reason': 'Selling DFEN at -20.0% loss (threshold: -10.0%)'}
```

#### 2.3 Post-Analysis Hook
Adds safety warnings to completed analysis.

**Checks:**
- High risk score (≥8/10)
- Elevated risk (≥6/10)
- Critical tail risk (≥8/10)
- Recommendations involving losses or leverage

### Configuration
```python
hooks = PortfolioSafetyHooks(constraints={
    'max_position_size': 0.35,           # 35% max per position
    'min_position_size': 0.05,           # 5% min per position
    'max_sector_exposure': 0.50,         # 50% max per sector
    'max_loss_threshold': -0.10,         # Warn on >10% loss
    'max_leverage': 1.0,                 # No leverage allowed
    'forbidden_symbols': ['TQQQ', 'SQQQ', 'UPRO', 'SPXU']
})
```

### Decision Types
- **allow**: Trade/operation permitted
- **deny**: Blocked (hard constraint violation)
- **warn**: Permitted with warning (soft constraint)

---

## 3. Background Tasks

### Purpose
Run long-running operations (Monte Carlo, Walk-Forward) without blocking main analysis.

### Implementation
Located in `src/tasks/background_tasks.py`

### Features

#### 3.1 Background Monte Carlo
```python
from src.tasks.background_tasks import BackgroundTaskManager

manager = BackgroundTaskManager()

# Start Monte Carlo in background
task_id = await manager.run_monte_carlo_background(
    task_id='mc_10k',
    historical_returns=returns,
    num_simulations=10000,
    horizon_days=252
)

# Check status
status = manager.get_status(task_id)
# Returns: {'status': 'running', 'progress': 0.45, 'started_at': '2025-10-04T18:00:00'}

# Get result when complete
result = manager.get_result(task_id)
```

**Progress Tracking:**
- Updates every 1,000 simulations
- Status: `running`, `completed`, `failed`, `cancelled`
- Progress: 0.0 to 1.0

#### 3.2 Background Walk-Forward
```python
task_id = await manager.run_walk_forward_background(
    task_id='wf_analysis',
    portfolio=portfolio,
    start_date='2020-01-01',
    end_date='2024-10-01',
    in_sample_window=252,
    out_sample_window=63,
    step_size=21
)

# Wait for completion
result = await manager.wait_for_task(task_id, timeout=600)
```

#### 3.3 Task Management
```python
# List all tasks
tasks = manager.list_tasks()
# Returns: {'mc_10k': {'status': 'completed', ...}, 'wf_analysis': {'status': 'running', ...}}

# Cancel running task
cancelled = await manager.cancel_task('mc_10k')

# Wait with timeout
result = await manager.wait_for_task('mc_10k', timeout=300)
```

### Performance
- **Monte Carlo (10K):** 60-90s (vs blocking main thread)
- **Walk-Forward (45 iter):** 5-8 min (runs in parallel with analysis)
- **Progress updates:** Every 1K simulations or 1 iteration

---

## 📊 Test Results

### Test Suite
Run `python test_new_features.py` to validate all features.

**Results (Oct 2024):**

#### Custom Tools ✅
- Real-time prices: VWCE.DE ($141.66), HYG ($80.84), AGGH.MI ($4.93)
- Portfolio metrics: HHI 0.559, Effective N 1.79
- Symbol check: SPY ✓, INVALID.XX ✗

#### Safety Hooks ✅
- Valid trade: ALLOW
- Oversized position (71%): **DENY**
- Forbidden TQQQ: **DENY**
- Large loss (-20%): **WARN**
- Pre-optimization: ALLOW (with default constraints)

#### Background Tasks ✅
- Monte Carlo (1000 sims): Completed in 3.2s
- Mean return: +65.81%, VaR 95%: 9.18%, Prob loss: 2.2%
- Progress tracking: ✓

---

## 🚀 Usage in Main System

### Integration Points

#### 1. Orchestrator (run_analysis.py)
Replace WebSearch for prices with custom tool:
```python
# OLD (30-60s)
market_data = await MarketDataAgent.get_data(symbols)

# NEW (2-5s)
prices = await CustomPortfolioTools.fetch_realtime_prices(symbols)
```

#### 2. Optimization Agent
Add pre-trade validation:
```python
hooks = PortfolioSafetyHooks()

for trade in recommended_trades:
    result = await hooks.pre_trade_hook(trade)

    if result['permissionDecision'] == 'deny':
        print(f"⛔ Trade blocked: {result['reason']}")
        continue
    elif result['permissionDecision'] == 'warn':
        print(f"⚠️  Warning: {result['reason']}")

    # Execute trade
    execute_trade(trade)
```

#### 3. Advanced Backtesting
Run Monte Carlo in background:
```python
# Start MC in background
task_id = await manager.run_monte_carlo_background(
    task_id='validation_mc',
    historical_returns=returns,
    num_simulations=10000
)

# Continue with walk-forward analysis
wf_results = await backtester.walk_forward_analysis(...)

# Get MC result when ready
mc_result = await manager.wait_for_task('validation_mc')
```

---

## 📈 Performance Improvements

| Operation | Before | After | Speedup |
|-----------|--------|-------|---------|
| Price fetch (4 symbols) | 30-60s | 2-5s | **10x** |
| Portfolio metrics | 20-40s (PortfolioAgent) | <1s | **30x** |
| Monte Carlo (10K) | Blocking (60s) | Background | **Non-blocking** |
| Trade validation | Manual | Automatic | **100% coverage** |

---

## ⚙️ Configuration

### Default Constraints
```python
DEFAULT_CONSTRAINTS = {
    'max_position_size': 0.35,
    'min_position_size': 0.05,
    'max_sector_exposure': 0.50,
    'max_loss_threshold': -0.10,
    'max_leverage': 1.0,
    'forbidden_symbols': []
}
```

### Custom Configuration
```python
# In run_analysis.py
from src.hooks.safety_hooks import PortfolioSafetyHooks

hooks = PortfolioSafetyHooks(constraints={
    'max_position_size': 0.30,  # More conservative
    'forbidden_symbols': ['TQQQ', 'SQQQ', 'UPRO', 'SPXU', 'DFEN']  # Block 3X ETFs
})
```

---

## 🔮 Future Enhancements

### Planned Features
1. **Tax Optimizer Agent** - Specialized subagent for tax-loss harvesting
2. **Memory System** - Store user preferences in CLAUDE.md
3. **Checkpointing** - Save portfolio state before rebalancing
4. **Custom MCP Servers** - External data integrations (Bloomberg, SEC filings)
5. **Slash Commands** - `/rebalance`, `/stress-test`, `/tax-optimize`

### Coming Soon
- Real-time streaming prices (WebSocket)
- Multi-currency support with FX hedging
- ESG scoring integration
- Options overlay strategies

---

## 📚 References

- [Claude Agent SDK Documentation](https://docs.claude.com/en/docs/claude-code/sdk/sdk-overview)
- [Building Agents with Claude SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Enabling Autonomous Work](https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously)

---

**Last Updated:** October 4, 2025
**Version:** 1.0.0
**Status:** ✅ Production Ready
