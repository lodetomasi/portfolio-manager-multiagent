"""
Safety Hooks for Portfolio Management
Provides automated validation and risk controls.
"""

from typing import Dict, Any, Optional
from datetime import datetime


class PortfolioSafetyHooks:
    """Hooks for trade validation and risk management"""

    def __init__(self, constraints: Optional[Dict] = None):
        """
        Initialize safety hooks with portfolio constraints.

        Args:
            constraints: {
                'max_position_size': 0.35,
                'min_position_size': 0.05,
                'max_sector_exposure': 0.50,
                'max_loss_threshold': -0.10,
                'max_leverage': 1.0,
                'forbidden_symbols': ['TQQQ', 'SQQQ']  # 3x leveraged ETFs
            }
        """
        self.constraints = constraints or {
            'max_position_size': 0.35,
            'min_position_size': 0.05,
            'max_sector_exposure': 0.50,
            'max_loss_threshold': -0.10,
            'max_leverage': 1.0,
            'forbidden_symbols': []
        }

    async def pre_optimization_hook(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook executed before optimization agent runs.
        Validates portfolio constraints and blocks dangerous operations.

        Args:
            input_data: Optimization input data

        Returns:
            {
                'permissionDecision': 'allow' | 'deny',
                'reason': str,
                'modified_constraints': Dict (optional)
            }
        """
        portfolio = input_data.get('portfolio', {})
        objective = input_data.get('objective', 'max_sharpe')

        # Check 1: Portfolio value too small for optimization
        total_value = portfolio.get('total_value', 0)
        if total_value < 1000:
            return {
                'permissionDecision': 'deny',
                'reason': f'Portfolio value too small for optimization (${total_value:.2f} < $1,000)',
                'timestamp': datetime.now().isoformat()
            }

        # Check 2: Validate objective
        valid_objectives = ['max_sharpe', 'min_variance', 'max_return', 'risk_parity']
        if objective not in valid_objectives:
            return {
                'permissionDecision': 'deny',
                'reason': f'Invalid objective: {objective}. Must be one of {valid_objectives}',
                'timestamp': datetime.now().isoformat()
            }

        # Check 3: Ensure constraints are present
        if not input_data.get('constraints'):
            return {
                'permissionDecision': 'allow',
                'reason': 'Adding default constraints',
                'modified_constraints': self.constraints,
                'timestamp': datetime.now().isoformat()
            }

        return {
            'permissionDecision': 'allow',
            'reason': 'Optimization validated',
            'timestamp': datetime.now().isoformat()
        }

    async def pre_trade_hook(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook executed before executing trades.
        Validates individual trades against risk limits.

        Args:
            trade_data: {
                'symbol': str,
                'action': 'BUY' | 'SELL',
                'shares': int,
                'price': float,
                'current_portfolio': Dict
            }

        Returns:
            {
                'permissionDecision': 'allow' | 'deny' | 'warn',
                'reason': str
            }
        """
        symbol = trade_data.get('symbol', '')
        action = trade_data.get('action', '')
        shares = trade_data.get('shares', 0)
        price = trade_data.get('price', 0)
        portfolio = trade_data.get('current_portfolio', {})

        # Check 1: Forbidden symbols (3x leveraged ETFs)
        forbidden = self.constraints.get('forbidden_symbols', [])
        if symbol in forbidden:
            return {
                'permissionDecision': 'deny',
                'reason': f'{symbol} is in forbidden list (high-risk leveraged instrument)',
                'timestamp': datetime.now().isoformat()
            }

        # Check 2: Detect 3x leverage by symbol pattern
        if any(pattern in symbol.upper() for pattern in ['3X', 'TQQQ', 'SQQQ', 'UPRO', 'SPXU']):
            return {
                'permissionDecision': 'warn',
                'reason': f'{symbol} appears to be a leveraged ETF - high risk warning',
                'timestamp': datetime.now().isoformat()
            }

        # Check 3: Position size limits (BUY only)
        if action == 'BUY':
            current_value = portfolio.get('total_value', 0)
            trade_value = shares * price
            new_value = current_value + trade_value
            position_weight = trade_value / new_value if new_value > 0 else 0

            max_pos = self.constraints.get('max_position_size', 0.35)
            if position_weight > max_pos:
                return {
                    'permissionDecision': 'deny',
                    'reason': f'Position size {position_weight:.1%} exceeds max {max_pos:.1%}',
                    'timestamp': datetime.now().isoformat()
                }

        # Check 4: Large loss detection (SELL only)
        if action == 'SELL':
            avg_cost = trade_data.get('average_cost', price)
            if avg_cost > 0:
                loss_pct = (price - avg_cost) / avg_cost
                max_loss = self.constraints.get('max_loss_threshold', -0.10)

                if loss_pct < max_loss:
                    return {
                        'permissionDecision': 'warn',
                        'reason': f'Selling {symbol} at {loss_pct:.1%} loss (threshold: {max_loss:.1%})',
                        'timestamp': datetime.now().isoformat()
                    }

        # Check 5: Zero shares or price
        if shares <= 0 or price <= 0:
            return {
                'permissionDecision': 'deny',
                'reason': f'Invalid trade: shares={shares}, price=${price:.2f}',
                'timestamp': datetime.now().isoformat()
            }

        return {
            'permissionDecision': 'allow',
            'reason': 'Trade validated',
            'timestamp': datetime.now().isoformat()
        }

    async def post_analysis_hook(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook executed after analysis completes.
        Validates recommendations and adds safety warnings.

        Args:
            analysis_result: Complete analysis output

        Returns:
            {
                'warnings': List[str],
                'risk_score': int,
                'action_required': bool
            }
        """
        warnings = []
        recommendations = analysis_result.get('recommendations', [])

        # Check for high-risk recommendations
        for rec in recommendations:
            if 'SELL' in rec.upper() and 'LOSS' in rec.upper():
                warnings.append(f'⚠️  Recommendation involves selling at loss: {rec[:100]}')

            if any(risky in rec.upper() for risky in ['3X', 'LEVERAGE', 'DERIVATIVE']):
                warnings.append(f'⚠️  High-risk instrument mentioned: {rec[:100]}')

        # Check risk score
        risk_score = analysis_result.get('risk_score', 0)
        if risk_score >= 8:
            warnings.append(f'🚨 Portfolio risk score {risk_score}/10 is CRITICAL - immediate action needed')
        elif risk_score >= 6:
            warnings.append(f'⚠️  Portfolio risk score {risk_score}/10 is elevated - review recommended')

        # Check tail risk
        tail_risk = analysis_result.get('tail_risk_score', 0)
        if tail_risk >= 8:
            warnings.append(f'🚨 Tail risk {tail_risk}/10 is CRITICAL - extreme downside exposure')

        return {
            'warnings': warnings,
            'risk_score': risk_score,
            'action_required': len(warnings) > 0,
            'timestamp': datetime.now().isoformat()
        }

    def get_hook_config(self) -> Dict[str, Any]:
        """
        Get hook configuration for Claude Agent SDK.

        Returns:
            Dict with hook functions and metadata
        """
        return {
            'pre_optimization': {
                'function': self.pre_optimization_hook,
                'description': 'Validate portfolio before optimization',
                'blocking': True
            },
            'pre_trade': {
                'function': self.pre_trade_hook,
                'description': 'Validate individual trades',
                'blocking': True
            },
            'post_analysis': {
                'function': self.post_analysis_hook,
                'description': 'Add safety warnings to analysis',
                'blocking': False
            }
        }
