"""
Multi-Agent Orchestrator using Claude Agent SDK

Coordinates multiple specialized agents to work in parallel on portfolio analysis.
"""

import asyncio
from typing import Dict, List
import json
from datetime import datetime

from agents.market_agent import MarketDataAgent
from agents.portfolio_agent import PortfolioAnalysisAgent
from agents.risk_agent import RiskAssessmentAgent
from agents.optimization_agent import PortfolioOptimizationAgent


class MultiAgentOrchestrator:
    """
    Orchestrates multiple Claude agents working in parallel.

    Execution Flow:
    Phase 1: Market Data Collection (sequential)
    Phase 2: Portfolio Analysis + Risk Assessment (parallel)
    Phase 3: Optimization (sequential, uses results from Phase 2)
    """

    def __init__(self):
        self.market_agent = MarketDataAgent()
        self.portfolio_agent = PortfolioAnalysisAgent()
        self.risk_agent = RiskAssessmentAgent()
        self.optimization_agent = PortfolioOptimizationAgent()

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {}

    async def run_full_analysis(
        self,
        portfolio: Dict,
        optimization_objective: str = "max_sharpe",
        constraints: Dict = None
    ) -> Dict:
        """
        Run complete multi-agent portfolio analysis.

        Args:
            portfolio: Portfolio holdings and cash
            optimization_objective: 'max_sharpe', 'min_variance', etc.
            constraints: Optimization constraints

        Returns:
            Comprehensive analysis results from all agents
        """
        print(f"\n{'='*70}")
        print(f"🤖 Multi-Agent Portfolio Analysis - Session {self.session_id}")
        print(f"{'='*70}\n")

        symbols = [h['symbol'] for h in portfolio['holdings']]

        # Default constraints
        if constraints is None:
            constraints = {
                "max_position_size": 0.35,
                "min_position_size": 0.05,
                "max_sector_exposure": 0.50
            }

        # ========== PHASE 1: Market Data Collection ==========
        print("📊 Phase 1: Collecting market data...")
        print("-" * 70)
        print(f"[LOG] Symbols to fetch: {', '.join(symbols)}")
        print("[LOG] Launching MarketDataAgent with WebSearch...")

        market_data = await self.market_agent.collect_data(symbols)
        self.results['market_data'] = market_data
        print(f"[LOG] Market data received: {len(market_data)} items")
        print("✓ Market data collected\n")

        # ========== PHASE 2: Parallel Analysis ==========
        print("📈 Phase 2: Running parallel analysis (Portfolio + Risk)...")
        print("-" * 70)
        print("[LOG] Creating parallel tasks...")

        # Run portfolio analysis and risk assessment in PARALLEL
        print("[LOG] Task 1: PortfolioAnalysisAgent starting...")
        portfolio_task = asyncio.create_task(
            self.portfolio_agent.analyze(portfolio, market_data)
        )
        print("[LOG] Task 2: RiskAssessmentAgent starting...")
        risk_task = asyncio.create_task(
            self.risk_agent.assess(portfolio, market_data)
        )

        print("[LOG] Waiting for both agents to complete (running in parallel)...")
        # Wait for both to complete
        portfolio_analysis, risk_assessment = await asyncio.gather(
            portfolio_task,
            risk_task
        )

        self.results['portfolio_analysis'] = portfolio_analysis
        self.results['risk_assessment'] = risk_assessment
        print("[LOG] PortfolioAnalysisAgent completed")
        print("✓ Portfolio analysis completed")
        print("[LOG] RiskAssessmentAgent completed")
        print("✓ Risk assessment completed\n")

        # ========== PHASE 3: Optimization ==========
        print("🎯 Phase 3: Generating optimal allocation...")
        print("-" * 70)
        print(f"[LOG] Optimization objective: {optimization_objective}")
        print(f"[LOG] Constraints: {constraints}")
        print("[LOG] Launching OptimizationAgent...")

        optimization = await self.optimization_agent.optimize(
            portfolio,
            market_data,
            constraints,
            optimization_objective
        )

        self.results['optimization'] = optimization
        print("[LOG] OptimizationAgent completed")
        print("✓ Optimization completed\n")

        # ========== CONSOLIDATE RESULTS ==========
        print("📋 Consolidating results...")
        print("-" * 70)

        final_report = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "portfolio": portfolio,
            "market_data": market_data,
            "analysis": {
                "portfolio_metrics": portfolio_analysis,
                "risk_assessment": risk_assessment,
                "optimization": optimization
            },
            "summary": self._generate_summary(
                portfolio_analysis,
                risk_assessment,
                optimization
            )
        }

        self.results['final_report'] = final_report

        print("✅ Multi-agent analysis complete!\n")
        print("=" * 70)

        return final_report

    def _generate_summary(
        self,
        portfolio_analysis: Dict,
        risk_assessment: Dict,
        optimization: Dict
    ) -> Dict:
        """Generate executive summary from all agent results"""

        summary = {
            "key_findings": [],
            "recommendations": [],
            "action_items": []
        }

        # Extract key metrics
        if 'portfolio_value' in portfolio_analysis:
            pv = portfolio_analysis['portfolio_value']
            summary['key_findings'].append(
                f"Portfolio Value: ${pv.get('total', 0):,.2f}"
            )

        if 'performance_metrics' in portfolio_analysis:
            pm = portfolio_analysis['performance_metrics']
            summary['key_findings'].append(
                f"Sharpe Ratio: {pm.get('sharpe_ratio', 0):.2f}"
            )
            summary['key_findings'].append(
                f"Max Drawdown: {pm.get('max_drawdown_pct', 0):.1f}%"
            )

        # Risk highlights
        if 'risk_scores' in risk_assessment:
            rs = risk_assessment['risk_scores']
            summary['key_findings'].append(
                f"Overall Risk Score: {rs.get('overall', 0)}/10"
            )

        if 'recommendations' in risk_assessment:
            summary['recommendations'].extend(risk_assessment['recommendations'])

        # Optimization actions
        if 'rebalancing_trades' in optimization:
            trades = optimization['rebalancing_trades']
            if trades:
                summary['action_items'].append(
                    f"Rebalancing: {len(trades)} trades recommended"
                )
                for trade in trades[:3]:  # Top 3 trades
                    action = f"{trade['action'].upper()} {trade['shares']} shares of {trade['symbol']}"
                    summary['action_items'].append(action)

        return summary

    def save_report(self, filepath: str = None):
        """Save final report to JSON file"""
        if filepath is None:
            filepath = f"portfolio_report_{self.session_id}.json"

        with open(filepath, 'w') as f:
            json.dump(self.results['final_report'], f, indent=2)

        print(f"💾 Report saved to: {filepath}")
        return filepath


async def main():
    """Example usage of multi-agent orchestrator"""

    # Example portfolio
    portfolio = {
        "name": "Tech-Heavy Growth Portfolio",
        "holdings": [
            {"symbol": "SPY", "shares": 100, "sector": "Broad Market"},
            {"symbol": "QQQ", "shares": 80, "sector": "Technology"},
            {"symbol": "GLD", "shares": 30, "sector": "Precious Metals"},
            {"symbol": "TLT", "shares": 40, "sector": "Bonds"}
        ],
        "cash": 15000
    }

    # Create orchestrator
    orchestrator = MultiAgentOrchestrator()

    # Run full analysis with agents working in parallel
    report = await orchestrator.run_full_analysis(
        portfolio=portfolio,
        optimization_objective="max_sharpe",
        constraints={
            "max_position_size": 0.40,
            "min_position_size": 0.05
        }
    )

    # Print summary
    print("\n📊 EXECUTIVE SUMMARY")
    print("=" * 70)
    print("\nKey Findings:")
    for finding in report['summary']['key_findings']:
        print(f"  • {finding}")

    print("\nRecommendations:")
    for rec in report['summary']['recommendations'][:5]:
        print(f"  • {rec}")

    print("\nAction Items:")
    for action in report['summary']['action_items']:
        print(f"  ➤ {action}")

    # Save report
    orchestrator.save_report()


if __name__ == "__main__":
    asyncio.run(main())
