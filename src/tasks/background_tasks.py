"""
Background Task Manager for Long-Running Operations
Uses asyncio to run Monte Carlo simulations and backtests without blocking.
"""

import asyncio
import json
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from dataclasses import asdict
import random


class BackgroundTaskManager:
    """Manages long-running tasks in background"""

    def __init__(self):
        self.tasks = {}
        self.results = {}
        self.status = {}

    async def run_monte_carlo_background(
        self,
        task_id: str,
        historical_returns: list,
        num_simulations: int = 10000,
        horizon_days: int = 252,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Run Monte Carlo simulation in background.

        Args:
            task_id: Unique task identifier
            historical_returns: List of daily returns
            num_simulations: Number of paths to simulate
            horizon_days: Forecast horizon (252 = 1 year)
            callback: Optional callback when complete

        Returns:
            Task ID for checking status
        """
        self.status[task_id] = {
            'status': 'running',
            'progress': 0,
            'started_at': datetime.now().isoformat()
        }

        async def monte_carlo_task():
            try:
                print(f"[BackgroundTask] Starting Monte Carlo ({num_simulations} simulations)...")

                simulated_returns = []

                for i in range(num_simulations):
                    # Bootstrap resampling
                    path_returns = [
                        random.choice(historical_returns)
                        for _ in range(horizon_days)
                    ]

                    # Calculate cumulative return
                    cumulative_return = 1.0
                    for r in path_returns:
                        cumulative_return *= (1 + r)

                    simulated_returns.append(cumulative_return - 1)

                    # Update progress every 1000 simulations
                    if (i + 1) % 1000 == 0:
                        progress = (i + 1) / num_simulations
                        self.status[task_id]['progress'] = progress
                        print(f"[BackgroundTask] Progress: {progress*100:.0f}%")

                # Sort for percentiles
                simulated_returns.sort()

                # Calculate statistics
                mean_return = sum(simulated_returns) / len(simulated_returns)
                median_return = simulated_returns[len(simulated_returns) // 2]

                # Calculate std
                variance = sum((r - mean_return) ** 2 for r in simulated_returns) / len(simulated_returns)
                std_return = variance ** 0.5

                # Percentiles
                percentile_5 = simulated_returns[int(0.05 * len(simulated_returns))]
                percentile_95 = simulated_returns[int(0.95 * len(simulated_returns))]

                # VaR and CVaR (Expected Shortfall)
                var_95 = abs(percentile_5)
                losses = [r for r in simulated_returns if r < 0]
                tail_losses = simulated_returns[:int(0.05 * len(simulated_returns))]
                expected_shortfall_95 = abs(sum(tail_losses) / len(tail_losses)) if tail_losses else 0

                # Probability of loss
                num_losses = sum(1 for r in simulated_returns if r < 0)
                probability_loss = num_losses / len(simulated_returns)

                result = {
                    'num_simulations': num_simulations,
                    'mean_return': mean_return,
                    'median_return': median_return,
                    'std_return': std_return,
                    'percentile_5': percentile_5,
                    'percentile_95': percentile_95,
                    'var_95': var_95,
                    'expected_shortfall_95': expected_shortfall_95,
                    'probability_loss': probability_loss,
                    'completed_at': datetime.now().isoformat()
                }

                self.results[task_id] = result
                self.status[task_id] = {
                    'status': 'completed',
                    'progress': 1.0,
                    'completed_at': datetime.now().isoformat()
                }

                print(f"[BackgroundTask] ✓ Monte Carlo complete")
                print(f"[BackgroundTask] Mean return: {mean_return*100:.2f}%")
                print(f"[BackgroundTask] VaR 95%: {var_95*100:.2f}%")
                print(f"[BackgroundTask] Prob of loss: {probability_loss*100:.1f}%")

                if callback:
                    await callback(result)

                return result

            except Exception as e:
                self.status[task_id] = {
                    'status': 'failed',
                    'error': str(e),
                    'failed_at': datetime.now().isoformat()
                }
                print(f"[BackgroundTask] ❌ Monte Carlo failed: {e}")
                raise

        # Start task in background
        task = asyncio.create_task(monte_carlo_task())
        self.tasks[task_id] = task

        return task_id

    async def run_walk_forward_background(
        self,
        task_id: str,
        portfolio: Dict,
        start_date: str,
        end_date: str,
        in_sample_window: int = 252,
        out_sample_window: int = 63,
        step_size: int = 21,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Run walk-forward analysis in background.

        Args:
            task_id: Unique task identifier
            portfolio: Portfolio configuration
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            in_sample_window: Training window (days)
            out_sample_window: Testing window (days)
            step_size: Rolling step (days)
            callback: Optional callback when complete

        Returns:
            Task ID for checking status
        """
        self.status[task_id] = {
            'status': 'running',
            'progress': 0,
            'started_at': datetime.now().isoformat()
        }

        async def walk_forward_task():
            try:
                print(f"[BackgroundTask] Starting Walk-Forward analysis...")

                # Import here to avoid circular dependency
                from ..backtesting.advanced_backtester import AdvancedBacktester

                backtester = AdvancedBacktester()

                results = await backtester.walk_forward_analysis(
                    portfolio=portfolio,
                    start_date=start_date,
                    end_date=end_date,
                    in_sample_window=in_sample_window,
                    out_sample_window=out_sample_window,
                    step_size=step_size
                )

                # Convert dataclass to dict
                results_dict = [asdict(r) for r in results]

                self.results[task_id] = {
                    'iterations': len(results_dict),
                    'results': results_dict,
                    'completed_at': datetime.now().isoformat()
                }

                self.status[task_id] = {
                    'status': 'completed',
                    'progress': 1.0,
                    'completed_at': datetime.now().isoformat()
                }

                print(f"[BackgroundTask] ✓ Walk-Forward complete ({len(results_dict)} iterations)")

                if callback:
                    await callback(results_dict)

                return results_dict

            except Exception as e:
                self.status[task_id] = {
                    'status': 'failed',
                    'error': str(e),
                    'failed_at': datetime.now().isoformat()
                }
                print(f"[BackgroundTask] ❌ Walk-Forward failed: {e}")
                raise

        # Start task in background
        task = asyncio.create_task(walk_forward_task())
        self.tasks[task_id] = task

        return task_id

    def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status of a background task.

        Args:
            task_id: Task identifier

        Returns:
            Status dict with 'status', 'progress', timestamps
        """
        return self.status.get(task_id, {'status': 'not_found'})

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get result of completed task.

        Args:
            task_id: Task identifier

        Returns:
            Result dict if completed, None otherwise
        """
        return self.results.get(task_id)

    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Wait for task to complete.

        Args:
            task_id: Task identifier
            timeout: Optional timeout in seconds

        Returns:
            Task result

        Raises:
            asyncio.TimeoutError: If timeout exceeded
            KeyError: If task not found
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found")

        task = self.tasks[task_id]

        if timeout:
            await asyncio.wait_for(task, timeout=timeout)
        else:
            await task

        return self.results.get(task_id, {})

    def list_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        List all tasks and their status.

        Returns:
            Dict with task_id -> status
        """
        return {
            task_id: self.get_status(task_id)
            for task_id in self.tasks.keys()
        }

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_id: Task identifier

        Returns:
            True if cancelled, False if not found or already completed
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        if not task.done():
            task.cancel()
            self.status[task_id] = {
                'status': 'cancelled',
                'cancelled_at': datetime.now().isoformat()
            }
            return True

        return False
