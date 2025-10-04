#!/usr/bin/env python3
"""
Portfolio Manager Multi-Agent CLI

This is the main entry point for the Portfolio Manager Multi-Agent System.
It generates specialized agent prompts that should be executed using Claude Code's Task tool.

Usage:
    python portfolio_manager.py --portfolio portfolio.json
    python portfolio_manager.py --sample  # Use sample portfolio
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.orchestrator import PortfolioOrchestrator
from agents.agent_configs import AGENT_TYPES, get_agent_system_prompt, get_execution_phases
from utils.market_data import create_sample_portfolio


def load_portfolio(filepath: str) -> dict:
    """Load portfolio from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)


def save_agent_prompts(agents_data: dict, output_dir: str = "agent_prompts"):
    """Save agent prompts to individual files for easy use with Claude Code"""
    Path(output_dir).mkdir(exist_ok=True)

    for agent_name, agent_info in agents_data.items():
        filepath = Path(output_dir) / f"{agent_name}_prompt.txt"
        with open(filepath, 'w') as f:
            f.write(f"AGENT: {agent_name}\n")
            f.write("=" * 60 + "\n\n")
            f.write(agent_info['prompt'])
            f.write("\n\n" + "=" * 60 + "\n")
            f.write(f"System Instructions:\n{get_agent_system_prompt(agent_name)}\n")

        print(f"✓ Saved {agent_name} prompt to {filepath}")


def print_execution_plan(phases: dict):
    """Print the execution plan for the multi-agent system"""
    print("\n" + "=" * 70)
    print("MULTI-AGENT EXECUTION PLAN")
    print("=" * 70)

    for phase_name, phase_info in phases.items():
        print(f"\n{phase_name.upper().replace('_', ' ')}:")
        print(f"  Description: {phase_info['description']}")
        print(f"  Parallel Execution: {phase_info['parallel']}")
        print(f"  Agents: {', '.join(phase_info['agents'])}")


def print_claude_code_instructions():
    """Print instructions for using with Claude Code"""
    print("\n" + "=" * 70)
    print("HOW TO RUN WITH CLAUDE CODE")
    print("=" * 70)
    print("""
This system is designed to work with Claude Code's Task tool for parallel agent execution.

OPTION 1: Manual Execution via Claude Code CLI
1. The agent prompts have been saved to the 'agent_prompts/' directory
2. Copy each prompt and use it with Claude Code
3. For parallel execution, run multiple Claude Code instances simultaneously

OPTION 2: Programmatic Execution (Recommended)
Use Claude Code to execute the agents by launching parallel Task tools:

Example workflow in Claude Code:
1. Ask Claude Code: "Launch the market-data agent with the prompt from agent_prompts/market-data_prompt.txt"
2. Then: "Launch portfolio-analysis, risk-assessment, and market-outlook agents in parallel"
3. Finally: "Launch the optimization agent after the analysis is complete"

OPTION 3: Automated Multi-Agent Execution
Tell Claude Code:
"I have a multi-agent portfolio management system. Please:
1. Read all prompts from the agent_prompts/ directory
2. Execute Phase 1 (market-data) first
3. Then execute Phase 2 agents (portfolio-analysis, risk-assessment, market-outlook) in PARALLEL
4. Finally execute Phase 3 (optimization) after Phase 2 completes
5. Consolidate all results into a comprehensive portfolio report"

The agents will work independently and Claude Code will coordinate their execution.
""")


def main():
    parser = argparse.ArgumentParser(
        description="Portfolio Manager Multi-Agent System - Generate agent prompts for Claude Code"
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
        '--output-dir',
        type=str,
        default='agent_prompts',
        help='Directory to save agent prompts (default: agent_prompts)'
    )
    parser.add_argument(
        '--show-plan',
        action='store_true',
        help='Show execution plan only'
    )

    args = parser.parse_args()

    # Load portfolio
    if args.sample or not args.portfolio:
        print("Using sample portfolio...")
        portfolio = create_sample_portfolio()
    else:
        print(f"Loading portfolio from {args.portfolio}...")
        portfolio = load_portfolio(args.portfolio)

    # Show execution plan if requested
    if args.show_plan:
        phases = get_execution_phases()
        print_execution_plan(phases)
        return

    # Extract symbols from portfolio
    symbols = [holding['symbol'] for holding in portfolio['holdings']]

    print(f"\n📊 Portfolio: {portfolio.get('name', 'Unnamed')}")
    print(f"📈 Symbols: {', '.join(symbols)}")
    print(f"💰 Cash: ${portfolio.get('cash', 0):,.2f}")

    # Create orchestrator and generate agent prompts
    orchestrator = PortfolioOrchestrator()
    result = orchestrator.run_parallel_analysis(portfolio, symbols)

    # Save prompts to files
    print(f"\n💾 Saving agent prompts to '{args.output_dir}/' directory...")
    save_agent_prompts(result['agents'], args.output_dir)

    # Show execution phases
    phases = get_execution_phases()
    print_execution_plan(phases)

    # Show Claude Code instructions
    print_claude_code_instructions()

    # Print summary
    print("\n" + "=" * 70)
    print("AGENT SUMMARY")
    print("=" * 70)
    for agent_name, agent_config in AGENT_TYPES.items():
        status = "✓" if agent_name in result['agents'] else "○"
        print(f"{status} {agent_config['name']}")
        print(f"   Priority: {agent_config['priority']} | Web: {agent_config['requires_web']}")
        print(f"   Tools: {', '.join(agent_config['tools_needed'])}")
        print()

    print("=" * 70)
    print("✅ Multi-Agent system ready!")
    print("📁 Agent prompts saved to:", args.output_dir)
    print("🚀 Use Claude Code to execute the agents")
    print("=" * 70)


if __name__ == "__main__":
    main()
