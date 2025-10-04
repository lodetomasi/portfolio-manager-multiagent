# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Portfolio Manager Multi-Agent system designed to act as an expert Quantitative Portfolio Manager with access to real-time market data and financial information. The system provides sophisticated portfolio analysis, optimization recommendations, and investment advice.

## Core System Behavior

The agent system is defined in `character.md` and follows these principles:

### Data-Driven Analysis Approach
- Actively uses web search for current market data, economic indicators, and asset performance
- Researches latest trends in sectors (semiconductors, energy, precious metals, etc.)
- Obtains up-to-date pricing for ETFs, stocks, and financial instruments
- Analyzes macroeconomic factors (interest rates, inflation, geopolitical events)

### Portfolio Construction Methodology
- Applies Modern Portfolio Theory, Post-Modern Portfolio Theory, and Factor-Based approaches
- Calculates key metrics: Sharpe ratio, maximum drawdown, risk-adjusted returns
- Creates efficient frontier analysis
- Provides mathematical justification for allocation recommendations

### Communication Standards
- Structured, professional format suitable for financial advising
- Uses appropriate financial terminology
- Clearly distinguishes factual market data from forward-looking opinions/forecasts
- Always cites sources of market data and financial information

## System Architecture

### Multi-Agent Orchestration
The system uses **Claude Code's Task tool** to orchestrate 5 specialized agents working in parallel:

1. **Market Data Agent** (`src/agents/orchestrator.py:create_market_data_agent_prompt`)
   - Collects real-time market data via web search
   - Gathers prices, volumes, news, analyst ratings
   - Priority: 1 (runs first)

2. **Portfolio Analysis Agent** (`src/agents/orchestrator.py:create_portfolio_analysis_agent_prompt`)
   - Calculates portfolio metrics (Sharpe, drawdown, volatility)
   - Performs attribution analysis
   - Priority: 2 (runs in parallel with risk & outlook)

3. **Risk Assessment Agent** (`src/agents/orchestrator.py:create_risk_assessment_agent_prompt`)
   - Analyzes portfolio risks (VaR, CVaR)
   - Runs stress test scenarios
   - Priority: 2 (runs in parallel)

4. **Market Outlook Agent** (`src/agents/orchestrator.py:create_market_outlook_agent_prompt`)
   - Provides forward-looking market analysis
   - Researches sector trends and macro conditions
   - Priority: 2 (runs in parallel)

5. **Optimization Agent** (`src/agents/orchestrator.py:create_optimization_agent_prompt`)
   - Calculates efficient frontier
   - Generates optimal allocation recommendations
   - Priority: 3 (runs after analysis agents)

### Execution Flow
```
Phase 1: market-data agent (sequential)
    ↓
Phase 2: portfolio-analysis, risk-assessment, market-outlook (parallel)
    ↓
Phase 3: optimization agent (sequential)
```

### Key Files
- `portfolio_manager.py` - Main CLI entry point, generates agent prompts
- `src/agents/orchestrator.py` - Multi-agent orchestration logic
- `src/agents/agent_configs.py` - Agent configurations and system prompts
- `src/utils/market_data.py` - Portfolio and market data utilities
- `src/utils/risk_analysis.py` - Risk metrics and stress testing

### Commands

**Generate agent prompts for Claude Code execution:**
```bash
python portfolio_manager.py --sample                    # Use sample portfolio
python portfolio_manager.py --portfolio <file.json>     # Use custom portfolio
python portfolio_manager.py --show-plan                 # Show execution plan
```

**Run the multi-agent system with Claude Code:**
After generating prompts, ask Claude Code to execute the agents following the phase plan.

## Development Guidelines

### When Building Portfolio Analysis Features
- Each portfolio analysis should begin with a current market overview using recent data
- Asset analysis must include current price, performance, and relevant news
- Asset allocation recommendations require precise percentage allocations and share quantities
- Market trends/forecasts should reference multiple expert perspectives
- Always highlight both opportunities AND risks

### Adding New Agents
1. Define agent configuration in `src/agents/agent_configs.py`
2. Add prompt generation method in `src/agents/orchestrator.py`
3. Update execution phases if needed
4. Add system prompt in `agent_configs.py:get_agent_system_prompt()`

### Quantitative Calculations
- Risk metrics implemented in `src/utils/risk_analysis.py`
- Portfolio utilities in `src/utils/market_data.py`
- Use Python stdlib (statistics, json) to avoid heavy dependencies
- All metrics follow Modern Portfolio Theory principles

### Data Integration
- Prioritize recent data (within past 30 days when possible)
- Synthesize information from multiple credible financial sources
- Apply critical thinking to conflicting market opinions
- Agents with web search capabilities cite all sources
