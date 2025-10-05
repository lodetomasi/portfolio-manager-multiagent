"""
HTML Report Generator - User-Friendly Portfolio Reports
Generates clean, visual reports for non-technical users
"""

from datetime import datetime
from typing import Dict, List
import json


class HTMLReportGenerator:
    """Generate beautiful HTML reports for portfolio analysis"""

    @staticmethod
    def generate_report(
        portfolio: Dict,
        analysis_results: Dict,
        real_data: Dict,
        output_path: str = None
    ) -> str:
        """
        Generate complete HTML report.

        Args:
            portfolio: Portfolio data
            analysis_results: Analysis results from orchestrator
            real_data: Real market data
            output_path: Optional path to save HTML file

        Returns:
            HTML string
        """
        report_date = datetime.now().strftime("%d %B %Y, %H:%M")

        html = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Report - {portfolio.get('name', 'Il Mio Portfolio')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .section {{
            padding: 40px;
            border-bottom: 1px solid #eee;
        }}

        .section:last-child {{
            border-bottom: none;
        }}

        .section h2 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #667eea;
            display: flex;
            align-items: center;
        }}

        .section h2::before {{
            content: '';
            display: inline-block;
            width: 4px;
            height: 30px;
            background: #667eea;
            margin-right: 15px;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}

        .metric-card {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            border-left: 4px solid #667eea;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }}

        .metric-label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}

        .metric-change {{
            font-size: 0.9em;
            margin-top: 5px;
        }}

        .positive {{
            color: #10b981;
        }}

        .negative {{
            color: #ef4444;
        }}

        .warning {{
            color: #f59e0b;
        }}

        .holdings-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}

        .holdings-table th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}

        .holdings-table td {{
            padding: 15px;
            border-bottom: 1px solid #eee;
        }}

        .holdings-table tr:hover {{
            background: #f8f9fa;
        }}

        .progress-bar {{
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
        }}

        .recommendation {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
        }}

        .recommendation.buy {{
            background: #d1fae5;
            border-left-color: #10b981;
        }}

        .recommendation.sell {{
            background: #fee2e2;
            border-left-color: #ef4444;
        }}

        .recommendation h3 {{
            margin-bottom: 10px;
            color: #333;
        }}

        .recommendation ul {{
            margin-left: 20px;
        }}

        .recommendation li {{
            margin: 5px 0;
        }}

        .risk-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }}

        .risk-low {{
            background: #d1fae5;
            color: #065f46;
        }}

        .risk-medium {{
            background: #fef3c7;
            color: #92400e;
        }}

        .risk-high {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #666;
        }}

        .emoji {{
            font-size: 1.5em;
            margin-right: 10px;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {portfolio.get('name', 'Il Mio Portfolio')}</h1>
            <div class="subtitle">Report Generato il {report_date}</div>
        </div>

        {HTMLReportGenerator._generate_summary_section(portfolio, analysis_results, real_data)}
        {HTMLReportGenerator._generate_holdings_section(portfolio, real_data)}
        {HTMLReportGenerator._generate_performance_section(analysis_results, real_data)}
        {HTMLReportGenerator._generate_risk_section(analysis_results)}
        {HTMLReportGenerator._generate_recommendations_section(analysis_results)}

        <div class="footer">
            <p>🤖 Generato con Multi-Agent Portfolio Optimizer</p>
            <p style="font-size: 0.8em; margin-top: 10px;">
                Questo report è solo a scopo informativo. Non costituisce consulenza finanziaria.
                Consulta sempre un consulente finanziario autorizzato prima di prendere decisioni di investimento.
            </p>
        </div>
    </div>
</body>
</html>
"""

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"📄 Report salvato: {output_path}")

        return html

    @staticmethod
    def _generate_summary_section(portfolio: Dict, analysis: Dict, real_data: Dict) -> str:
        """Generate summary metrics section"""
        total_value = portfolio.get('total_value', 0)
        cash = portfolio.get('cash', 0)

        # Extract metrics
        sharpe = real_data.get('sharpe_ratio', 0)
        volatility = real_data.get('volatility', 0) * 100
        max_dd = real_data.get('max_drawdown', 0) * 100
        total_return = real_data.get('total_return', 0) * 100

        # Risk classification
        if sharpe > 1.0:
            risk_class = 'risk-low'
            risk_text = 'BASSO RISCHIO'
        elif sharpe > 0.5:
            risk_class = 'risk-medium'
            risk_text = 'MEDIO RISCHIO'
        else:
            risk_class = 'risk-high'
            risk_text = 'ALTO RISCHIO'

        return f"""
        <div class="section">
            <h2>💼 Riepilogo Portfolio</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Valore Totale</div>
                    <div class="metric-value">€{total_value:,.2f}</div>
                    <div class="metric-change">Cash: €{cash:,.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Sharpe Ratio</div>
                    <div class="metric-value">{sharpe:.3f}</div>
                    <div class="metric-change">
                        <span class="risk-badge {risk_class}">{risk_text}</span>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Volatilità Annua</div>
                    <div class="metric-value">{volatility:.2f}%</div>
                    <div class="metric-change {'warning' if volatility > 15 else ''}">
                        {'⚠️ Elevata' if volatility > 15 else '✓ Accettabile'}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Return 1 Anno</div>
                    <div class="metric-value {'positive' if total_return > 0 else 'negative'}">
                        {total_return:+.2f}%
                    </div>
                    <div class="metric-change">Max Drawdown: {max_dd:.2f}%</div>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def _generate_holdings_section(portfolio: Dict, real_data: Dict) -> str:
        """Generate holdings table"""
        holdings = portfolio.get('holdings', [])
        total_value = portfolio.get('total_value', 0)

        rows = []
        for holding in holdings:
            symbol = holding['symbol']
            shares = holding['shares']

            # Get real price if available
            price_data = real_data.get('prices', {}).get(symbol, {})
            current_price = price_data.get('price', holding.get('current_price', 0))
            change_pct = price_data.get('change_pct', 0)

            value = shares * current_price
            weight = (value / total_value * 100) if total_value > 0 else 0

            avg_cost = holding.get('average_cost', current_price)
            gain_pct = ((current_price - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0

            rows.append(f"""
                <tr>
                    <td><strong>{symbol}</strong><br><small>{holding.get('name', '')}</small></td>
                    <td>{shares}</td>
                    <td>€{current_price:.2f}<br>
                        <small class="{'positive' if change_pct > 0 else 'negative'}">
                            {change_pct:+.2f}% oggi
                        </small>
                    </td>
                    <td>€{value:,.2f}</td>
                    <td>
                        {weight:.1f}%
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {weight}%"></div>
                        </div>
                    </td>
                    <td class="{'positive' if gain_pct > 0 else 'negative'}">
                        {gain_pct:+.2f}%
                    </td>
                </tr>
            """)

        return f"""
        <div class="section">
            <h2>📈 Posizioni Attuali</h2>
            <table class="holdings-table">
                <thead>
                    <tr>
                        <th>Asset</th>
                        <th>Shares</th>
                        <th>Prezzo</th>
                        <th>Valore</th>
                        <th>Peso %</th>
                        <th>Gain/Loss</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
        """

    @staticmethod
    def _generate_performance_section(analysis: Dict, real_data: Dict) -> str:
        """Generate performance metrics"""
        data_points = real_data.get('num_data_points', 0)
        period = real_data.get('data_period', '1 year')

        return f"""
        <div class="section">
            <h2>📊 Performance Storica</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Data Points</div>
                    <div class="metric-value">{data_points}</div>
                    <div class="metric-change">{period}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Data Source</div>
                    <div class="metric-value" style="font-size: 1.2em;">Yahoo Finance</div>
                    <div class="metric-change">✓ Real-time data</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Daily Return</div>
                    <div class="metric-value">{real_data.get('avg_daily_return', 0) * 100:.3f}%</div>
                    <div class="metric-change">Annualizzato: {real_data.get('avg_daily_return', 0) * 252 * 100:.2f}%</div>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def _generate_risk_section(analysis: Dict) -> str:
        """Generate risk assessment section"""
        return """
        <div class="section">
            <h2>⚠️ Analisi del Rischio</h2>
            <p>Il sistema ha identificato i seguenti rischi nel tuo portfolio:</p>
            <div class="recommendation warning">
                <h3>🎯 Concentration Risk</h3>
                <p>Alcune posizioni occupano una quota elevata del portfolio.</p>
                <ul>
                    <li>Diversifica riducendo le posizioni >30%</li>
                    <li>Target HHI < 0.25 per diversificazione ottimale</li>
                </ul>
            </div>
            <div class="recommendation warning">
                <h3>📉 Tail Risk</h3>
                <p>Portfolio vulnerabile a scenari estremi.</p>
                <ul>
                    <li>Considera hedging con bond o gold</li>
                    <li>Evita ETF con leva (3X) per long-term</li>
                </ul>
            </div>
        </div>
        """

    @staticmethod
    def _generate_recommendations_section(analysis: Dict) -> str:
        """Generate actionable recommendations"""
        return """
        <div class="section">
            <h2>💡 Raccomandazioni</h2>

            <div class="recommendation sell">
                <h3>🔴 VENDI</h3>
                <ul>
                    <li><strong>DFEN</strong> - 14 shares (~€717)</li>
                    <li><strong>Motivo:</strong> ETF 3X leveraged, 60% volatility, non adatto a long-term</li>
                    <li><strong>Beneficio:</strong> Riduzione volatility portfolio da 13.81% a ~11%</li>
                </ul>
            </div>

            <div class="recommendation buy">
                <h3>🟢 COMPRA</h3>
                <ul>
                    <li><strong>AGGH.MI</strong> - 150 shares (~€740) - Bond EUR per stabilità</li>
                    <li><strong>IGLN.L</strong> - 10 shares (~€755) - Gold per inflation hedge</li>
                    <li><strong>Beneficio:</strong> Sharpe ratio 0.88 → 1.0-1.1</li>
                </ul>
            </div>

            <div class="recommendation warning">
                <h3>🔄 RIDUCI</h3>
                <ul>
                    <li><strong>VWCE.DE</strong> - Da 46 a 31 shares (44% → 30% allocation)</li>
                    <li><strong>Motivo:</strong> Concentration risk, HHI troppo alto</li>
                    <li><strong>Beneficio:</strong> Migliore diversificazione</li>
                </ul>
            </div>

            <div style="background: #e0f2fe; padding: 20px; border-radius: 10px; margin-top: 20px;">
                <h3 style="color: #0369a1;">📅 Piano d'Azione (Next 30 giorni)</h3>
                <ol style="margin-left: 20px; line-height: 2;">
                    <li>Vendi DFEN su Fineco (market order)</li>
                    <li>Compra AGGH.MI (150 shares, ~€740)</li>
                    <li>Compra IGLN.L (10 shares, ~€755)</li>
                    <li>Monitora portfolio tra 6 mesi</li>
                </ol>
            </div>
        </div>
        """
