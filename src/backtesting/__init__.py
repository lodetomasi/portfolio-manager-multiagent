"""
Backtesting Module

Provides comprehensive backtesting and validation capabilities
for portfolio management strategies.
"""

from .backtester import PortfolioBacktester, BacktestResult, BacktestPeriod
from .historical_data import HistoricalDataFetcher, RealTimeDataAdapter
from .performance import PerformanceCalculator

__all__ = [
    'PortfolioBacktester',
    'BacktestResult',
    'BacktestPeriod',
    'HistoricalDataFetcher',
    'RealTimeDataAdapter',
    'PerformanceCalculator'
]
