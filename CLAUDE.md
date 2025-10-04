# Multi-Agent System Design: Anthropic Best Practices

This document captures the core principles and implementation patterns used in this multi-agent portfolio management system, based on Anthropic's research on multi-agent architectures.

**Reference**: [Anthropic Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)

---

## Core Architecture Pattern: Orchestrator-Worker

### Principle
A lead orchestrator coordinates specialized subagents, each with narrow expertise and explicit task boundaries.

### Implementation
```python
class MultiAgentOrchestrator:
    def __init__(self):
        # Specialized worker agents
        self.market_agent = MarketDataAgent()
        self.portfolio_agent = PortfolioAnalysisAgent()
        self.risk_agent = RiskAssessmentAgent()
        self.optimization_agent = PortfolioOptimizationAgent()

        # Explicit task assignments to prevent duplicate work
        self.task_assignments = {
            "market_data": "Collect real-time prices, volumes, news - DO NOT analyze",
            "portfolio_analysis": "Calculate MPT metrics - DO NOT assess risks or optimize",
            "risk_assessment": "Quantify risks and stress test - DO NOT optimize allocation",
            "optimization": "Generate optimal allocation - Uses results from analysis/risk"
        }
```

### Why It Works
- **Specialization**: Each agent becomes expert in narrow domain
- **No overlap**: Clear boundaries prevent redundant computation
- **Composability**: Orchestrator combines results into coherent output

---

## Rule 1: Progressive Search Strategy

### Principle
Start broad, evaluate quality, narrow focus based on findings. Avoid immediate deep dives.

### Implementation (MarketDataAgent)
```python
system_prompt = """
PROGRESSIVE SEARCH STRATEGY:
1. Start BROAD: Query all symbols together first
2. Evaluate QUALITY: Check source reliability (Bloomberg, Reuters, official exchanges)
3. Narrow FOCUS: If incomplete, search specific symbols individually
4. Self-ADAPT: Adjust based on findings

RESOURCE ALLOCATION (Critical):
- Maximum 3-4 web searches total
- Stop when complete data obtained
- Each search should maximize information gain
- Prioritize reliable sources
"""
```

### Example Execution
```
Search 1: "DEFX.MI VWCE.DE HYGG.PA AEEM.PA current price" → Gets 3/4 symbols
Search 2: "AEEM.PA price EUR" → Completes missing data
✓ Stop (all data obtained, 2 searches used)
```

### Anti-Pattern
```
❌ Search 1: "DEFX.MI detailed analysis"
❌ Search 2: "VWCE.DE comprehensive report"
❌ Search 3: "HYGG.PA full metrics"
❌ Search 4: "AEEM.PA complete data"
(Redundant, inefficient, exceeds resource budget)
```

---

## Rule 2: Explicit Task Scoping

### Principle
Each agent must know exactly what it SHOULD do and what it SHOULD NOT do. Use explicit "DO NOT" constraints.

### Implementation (All Agents)

**PortfolioAgent**:
```python
EXPLICIT TASK SCOPE (Critical):
- Calculate MPT metrics ONLY
- DO NOT assess risks (RiskAgent's job)
- DO NOT optimize allocation (OptimizationAgent's job)
- DO NOT search for external data (already provided)
```

**RiskAgent**:
```python
EXPLICIT TASK SCOPE (Critical):
- Quantify risks and run stress tests ONLY
- DO NOT calculate Sharpe/returns (PortfolioAgent's job)
- DO NOT optimize allocation (OptimizationAgent's job)
- DO NOT collect market data (already provided)
```

**OptimizationAgent**:
```python
EXPLICIT TASK SCOPE (Critical):
- Generate optimal allocation and trades ONLY
- DO NOT calculate current Sharpe/metrics (PortfolioAgent already did)
- DO NOT run stress tests (RiskAgent already did)
- DO NOT search for market data (already provided)
```

### Why It Matters
Without explicit boundaries, agents will:
1. Duplicate work already done by other agents
2. Exceed resource budgets (time, API calls)
3. Produce conflicting results
4. Waste computational resources

---

## Rule 3: Resource Allocation Guidelines

### Principle
Every agent must operate within defined resource budgets. Make budgets explicit in system prompts.

### Implementation

**MarketDataAgent**:
```
RESOURCE ALLOCATION:
- Maximum 3-4 web searches total
- Stop when complete data obtained
- Each search should maximize information gain
```

**PortfolioAgent**:
```
RESOURCE ALLOCATION:
- Use provided market data - NO web searches
- Maximum 2-3 bash calculations if needed
- Focus on accuracy over exhaustive analysis
- Stop when core metrics computed
```

**RiskAgent**:
```
RESOURCE ALLOCATION:
- Maximum 1-2 web searches ONLY if critical volatility data missing
- Run 5 core stress scenarios (no more)
- Focus on downside risk quantification
```

**OptimizationAgent**:
```
RESOURCE ALLOCATION:
- Use provided data exclusively - NO web searches
- Maximum 3-5 bash commands for optimization
- Compute 8-10 efficient frontier points
- Focus on feasible, actionable trades
```

### Timeout Safety
```python
async with asyncio.timeout(120):  # 2-minute max per agent
    async for message in query(prompt, options):
        process(message)
```

---

## Rule 4: Avoid Duplicate Work

### Principle
Track what data/calculations already exist. Don't recompute what other agents have already done.

### Implementation

**In System Prompts**:
```python
AVOID DUPLICATE WORK:
- PortfolioAgent handles: Sharpe, correlations, attribution
- RiskAgent handles: VaR, CVaR, stress tests
- OptimizationAgent handles: rebalancing, efficient frontier
- You handle ONLY: [specific scope]
```

**In Orchestrator**:
```python
# Phase 2: Pass market_data from Phase 1 (don't re-fetch)
portfolio_analysis = await portfolio_agent.analyze(portfolio, market_data)

# Phase 3: Pass results from Phase 2 (don't recalculate)
optimization = await optimization_agent.optimize(
    portfolio,
    market_data,  # From Phase 1
    constraints,
    optimization_objective
)
```

### Anti-Pattern
```python
❌ # RiskAgent recalculating Sharpe ratio
❌ sharpe = calculate_sharpe(...)  # PortfolioAgent already did this!

❌ # OptimizationAgent re-fetching prices
❌ prices = web_search("current prices")  # MarketDataAgent already has this!
```

---

## Rule 5: Extended Thinking / Transparency

### Principle
Make agent reasoning and orchestrator decisions visible through structured logging.

### Implementation (Orchestrator)
```python
print(f"[ORCHESTRATOR] Task assignment: {self.task_assignments['market_data']}")
print(f"[ORCHESTRATOR] Symbols to fetch: {', '.join(symbols)}")
print(f"[ORCHESTRATOR] Expected effort: 3-4 web searches, ~30-60s")
print("[ORCHESTRATOR] Launching MarketDataAgent with WebSearch tools...")

# After execution
if 'error' in market_data:
    print(f"[ORCHESTRATOR] ⚠️  Market data collection failed: {market_data['error']}")
else:
    symbols_found = len(market_data.get('symbols', {}))
    print(f"[ORCHESTRATOR] ✓ Symbols retrieved: {symbols_found}/{len(symbols)}")
```

### Benefits
1. **Debugging**: Quickly identify which agent failed
2. **User trust**: Transparent about what system is doing
3. **Performance monitoring**: Track execution time per phase
4. **Error diagnosis**: Pinpoint exact failure point

---

## Rule 6: Quality Standards

### Principle
Define explicit quality expectations and validation rules for each agent.

### Implementation

**PortfolioAgent**:
```python
QUALITY STANDARDS:
- Show all formulas and calculations
- Use industry-standard methodologies (MPT)
- Validate calculations (e.g., weights sum to 1.0)
- Flag any data quality concerns
```

**RiskAgent**:
```python
QUALITY STANDARDS:
- Use coherent risk measures (CVaR per Rockafellar & Uryasev)
- Validate stress test assumptions
- Cite volatility sources if searching web
- Flag low-confidence estimates explicitly
```

**OptimizationAgent**:
```python
QUALITY STANDARDS:
- Use Markowitz mean-variance optimization
- Validate constraints satisfaction (weights sum to 1.0)
- Consider transaction costs ($5 per trade)
- Ensure trades are executable (integer shares)
- Provide clear rationale citing MPT principles
```

**MarketDataAgent**:
```python
Data Quality Standards:
- Cite sources with dates
- Prioritize last 24-48 hours
- Cross-reference when possible
- Flag uncertain data explicitly
```

---

## Rule 7: Parallel Execution Where Safe

### Principle
Run independent agents concurrently to improve performance. Only run sequentially when dependencies exist.

### Implementation
```python
# ✓ Safe to parallelize (no shared state, independent analyses)
portfolio_task = asyncio.create_task(portfolio_agent.analyze(portfolio, market_data))
risk_task = asyncio.create_task(risk_agent.assess(portfolio, market_data))

portfolio_analysis, risk_assessment = await asyncio.gather(
    portfolio_task,
    risk_task
)
```

### Dependency Graph
```
Phase 1: MarketDataAgent (sequential - foundation)
           ↓
Phase 2: PortfolioAgent ║ RiskAgent (parallel - independent)
           ↓
Phase 3: OptimizationAgent (sequential - depends on Phase 2)
```

### Performance Impact
- **Sequential**: ~150s total
- **With Phase 2 parallel**: ~90s total
- **Speedup**: 1.67x

### Safety Requirements
1. **Session isolation**: Each agent gets own Claude session
2. **No shared mutable state**: Agents only read inputs
3. **No race conditions**: Results combined after both complete

---

## Rule 8: Explicit Dependencies

### Principle
When one agent depends on another's output, document this clearly in system prompts.

### Implementation (OptimizationAgent)
```python
DEPENDENCIES (Use Results From):
- PortfolioAgent: Current weights, Sharpe, volatility, correlations
- RiskAgent: Risk scores, concentration metrics, VaR
- MarketDataAgent: Prices, expected returns, volatilities
```

### In Orchestrator
```python
# Phase 3 explicitly depends on Phase 2 results
optimization = await optimization_agent.optimize(
    portfolio,
    market_data,      # Dependency: Phase 1
    constraints,
    optimization_objective
)
# Pass Phase 2 results in context, not as separate args
# Agent accesses via prompt context
```

---

## Rule 9: Tool Permission Constraints

### Principle
Grant each agent only the minimal tools needed for its specific task. Security through least privilege.

### Implementation
```python
# MarketDataAgent: Needs to fetch external data
ClaudeAgentOptions(
    system_prompt=self.system_prompt,
    allowed_tools=["WebSearch", "WebFetch"]
)

# PortfolioAgent: Only local calculations
ClaudeAgentOptions(
    system_prompt=self.system_prompt,
    allowed_tools=["Bash"]  # Can run Python calculations
)

# RiskAgent: Sometimes needs volatility data
ClaudeAgentOptions(
    system_prompt=self.system_prompt,
    allowed_tools=["Bash", "WebSearch"]
)

# OptimizationAgent: Only local calculations
ClaudeAgentOptions(
    system_prompt=self.system_prompt,
    allowed_tools=["Bash"]
)
```

### Security Benefits
1. **Scope creep prevention**: Agent can't exceed mandate
2. **Cost control**: Limits expensive API calls (WebSearch)
3. **Reproducibility**: Local calculations deterministic
4. **Audit trail**: Clear which agent made which external calls

---

## Rule 10: Stop Conditions

### Principle
Define explicit stop conditions to prevent infinite loops or excessive computation.

### Implementation

**In System Prompts**:
```python
IMPORTANT STOP CONDITIONS:
- Do ONE web search per symbol to get current data
- DO NOT continue searching after you have basic data for all symbols
- IMMEDIATELY return JSON once you have prices and basic info
- DO NOT overthink or search for additional context
- Maximum 2-3 searches total
```

**In Code**:
```python
# Timeout as hard stop
async with asyncio.timeout(120):
    async for message in query(prompt, options):
        process(message)
```

**In Prompts**:
```python
prompt = f"""
Tasks:
1. Calculate X
2. Compute Y
3. Generate Z

Return ONLY valid JSON matching the specified format and STOP.
"""
```

### Why Critical
Without stop conditions:
- Agents continue searching indefinitely
- Costs accumulate (API calls, compute time)
- User experience degrades (long wait times)
- Timeouts trigger, losing partial progress

---

## Validation Checklist

Use this checklist when implementing new agents:

### Agent Design
- [ ] System prompt includes "EXPLICIT TASK SCOPE"
- [ ] Lists what agent SHOULD do
- [ ] Lists what agent SHOULD NOT do (with specific other agents mentioned)
- [ ] Defines resource allocation limits (searches, bash commands, time)
- [ ] Includes quality standards section
- [ ] Defines explicit stop conditions
- [ ] Specifies output format (usually JSON schema)

### Tool Configuration
- [ ] `allowed_tools` includes only minimum required tools
- [ ] WebSearch only if agent truly needs external data
- [ ] Bash only if calculations needed

### Orchestrator Integration
- [ ] Task description added to `task_assignments` dict
- [ ] Logging includes [ORCHESTRATOR] prefix
- [ ] Logs task assignment before agent launch
- [ ] Logs resource expectations (time, searches)
- [ ] Validates results after agent completes
- [ ] Logs success metrics or error details

### Execution
- [ ] Timeout wrapper (`asyncio.timeout`) in place
- [ ] Proper error handling for parsing failures
- [ ] Results passed to downstream agents (no recomputation)

### Documentation
- [ ] Agent's role documented in README
- [ ] Dependencies on other agents documented
- [ ] Example output provided

---

## Performance Optimization Strategies

### 1. Caching Layer (Future Enhancement)
```python
class MarketDataAgent:
    def __init__(self):
        self.cache = {}  # symbol -> {data, timestamp}
        self.cache_ttl = 300  # 5 minutes

    async def collect_data(self, symbols):
        # Check cache first
        cached = {s: self.cache[s] for s in symbols
                  if s in self.cache and not_expired(self.cache[s])}

        # Only fetch uncached symbols
        to_fetch = [s for s in symbols if s not in cached]
        if to_fetch:
            fresh = await self._fetch(to_fetch)
            self.cache.update(fresh)

        return {**cached, **fresh}
```

### 2. Batch Processing
```python
# ✓ Good: Process all symbols together
symbols = ["SPY", "QQQ", "GLD", "TLT"]
data = await market_agent.collect_data(symbols)

# ❌ Bad: Serial individual requests
for symbol in symbols:
    data[symbol] = await market_agent.collect_data([symbol])
```

### 3. Early Termination
```python
# In agent prompt
"""
If you determine the current allocation is already optimal (within 2% of theoretical max Sharpe):
- Set rebalancing_trades to []
- Explain why no changes needed
- STOP immediately (don't compute full efficient frontier)
"""
```

---

## Common Anti-Patterns

### ❌ Agent Scope Creep
```python
# RiskAgent system prompt (BAD)
"""Calculate risks AND provide optimization recommendations"""
# Problem: Optimization is OptimizationAgent's job
```

### ❌ Redundant Searches
```python
# MarketDataAgent searches, then RiskAgent re-searches same data
# Solution: Pass market_data from Phase 1 to Phase 2
```

### ❌ Implicit Dependencies
```python
# OptimizationAgent prompt (BAD)
"""Optimize the portfolio"""
# Problem: Doesn't specify it uses PortfolioAgent and RiskAgent results

# GOOD:
"""
Using the portfolio metrics from PortfolioAgent and risk scores from RiskAgent,
generate optimal allocation...
"""
```

### ❌ Unbounded Loops
```python
# Agent prompt (BAD)
"""Search until you find comprehensive data"""
# Problem: "comprehensive" is unbounded

# GOOD:
"""Search maximum 3 times. After 3 searches, return best available data."""
```

### ❌ Missing Error Validation
```python
# Orchestrator (BAD)
market_data = await market_agent.collect_data(symbols)
# Immediately pass to next phase without checking for errors

# GOOD:
market_data = await market_agent.collect_data(symbols)
if 'error' in market_data:
    print(f"[ORCHESTRATOR] ⚠️  Failed: {market_data['error']}")
    # Handle gracefully
```

---

## Measuring Success

### Key Metrics

**Resource Efficiency**:
- WebSearch calls per analysis: Target < 5
- Total execution time: Target < 120s
- Claude API tokens: Monitor per agent

**Quality Metrics**:
- JSON parse success rate: Target 100%
- Data completeness: All symbols found
- Calculation accuracy: Weights sum to 1.0 ± 0.001

**Coordination Metrics**:
- Duplicate work incidents: Target 0
- Task boundary violations: Target 0
- Parallel speedup ratio: Target > 1.5x

### Monitoring Code
```python
class MultiAgentOrchestrator:
    def __init__(self):
        self.metrics = {
            'web_searches': 0,
            'execution_time': {},
            'errors': []
        }

    async def run_full_analysis(self, ...):
        start_time = time.time()

        # Track per phase
        phase1_start = time.time()
        market_data = await self.market_agent.collect_data(symbols)
        self.metrics['execution_time']['phase1'] = time.time() - phase1_start

        # Log at end
        print(f"\n📊 Performance Metrics:")
        print(f"  Total time: {time.time() - start_time:.1f}s")
        print(f"  Phase breakdown: {self.metrics['execution_time']}")
```

---

## References

1. **Anthropic Multi-Agent Research System**
   https://www.anthropic.com/engineering/multi-agent-research-system

2. **Modern Portfolio Theory (Markowitz, 1952)**
   Foundation for PortfolioAgent calculations

3. **Coherent Risk Measures (Rockafellar & Uryasev, 2000)**
   CVaR implementation in RiskAgent

4. **Python asyncio Documentation**
   Parallel execution patterns

---

## Revision History

- **2025-10-04**: Initial documentation based on Anthropic best practices implementation
- Applied to 4-agent portfolio management system
- Validated through production testing
