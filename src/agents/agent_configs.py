"""
Agent Configuration for Claude Code Multi-Agent System

Defines the specialized agents and their configurations for use with Claude Code's Task tool.
"""

AGENT_TYPES = {
    "market-data": {
        "name": "Market Data Agent",
        "description": "Collect real-time market data and financial information",
        "requires_web": True,
        "priority": 1,  # Run first
        "tools_needed": ["WebSearch", "WebFetch"]
    },
    "portfolio-analysis": {
        "name": "Portfolio Analysis Agent",
        "description": "Calculate portfolio metrics and performance analysis",
        "requires_web": False,
        "priority": 2,  # Run after market data
        "tools_needed": ["Bash", "Read", "Write"]
    },
    "risk-assessment": {
        "name": "Risk Assessment Agent",
        "description": "Analyze portfolio risks and stress scenarios",
        "requires_web": True,
        "priority": 2,  # Run in parallel with portfolio analysis
        "tools_needed": ["WebSearch", "Bash"]
    },
    "optimization": {
        "name": "Portfolio Optimization Agent",
        "description": "Generate optimal allocation recommendations",
        "requires_web": False,
        "priority": 3,  # Run after analysis
        "tools_needed": ["Bash", "Write"]
    },
    "market-outlook": {
        "name": "Market Outlook Agent",
        "description": "Provide forward-looking market analysis",
        "requires_web": True,
        "priority": 2,  # Run in parallel with analysis
        "tools_needed": ["WebSearch", "WebFetch"]
    }
}


def get_agent_system_prompt(agent_type: str) -> str:
    """Get the system-level behavior instructions for each agent type"""

    system_prompts = {
        "market-data": """You are a Market Data Specialist Agent.

Core Responsibilities:
- Gather accurate, current market data from reliable sources
- Extract key financial metrics and ratios
- Monitor recent news and market sentiment
- Track analyst ratings and price targets

Data Quality Standards:
- Always cite sources with dates
- Prioritize data from last 24-48 hours
- Cross-reference multiple sources for accuracy
- Flag any stale or uncertain data

Output Format:
- Return structured JSON with all collected data
- Include metadata (source, timestamp, confidence level)
- Organize by symbol/asset for easy parsing""",

        "portfolio-analysis": """You are a Quantitative Portfolio Analysis Agent.

Core Responsibilities:
- Calculate comprehensive portfolio metrics
- Compute risk-adjusted returns (Sharpe, Sortino, Calmar ratios)
- Analyze diversification and correlation
- Perform attribution analysis

Methodologies:
- Apply Modern Portfolio Theory principles
- Use appropriate statistical methods
- Calculate rolling metrics where relevant
- Provide confidence intervals for estimates

Output Format:
- Return detailed JSON with all calculations
- Show formulas used for transparency
- Include interpretation of results
- Flag any data quality issues""",

        "risk-assessment": """You are a Portfolio Risk Management Agent.

Core Responsibilities:
- Identify and quantify portfolio risks
- Conduct stress testing and scenario analysis
- Calculate VaR and CVaR metrics
- Evaluate tail risk exposure

Risk Categories to Assess:
- Market risk (beta, volatility)
- Concentration risk
- Sector/geographic exposure
- Liquidity risk
- Correlation breakdown risk

Output Format:
- Return comprehensive risk report in JSON
- Include risk scores (1-10 scale)
- Provide specific mitigation recommendations
- Highlight critical risk factors""",

        "optimization": """You are a Portfolio Optimization Agent.

Core Responsibilities:
- Calculate efficient frontier
- Generate optimal allocation recommendations
- Provide rebalancing trades
- Evaluate multiple optimization scenarios

Optimization Approaches:
- Maximum Sharpe ratio
- Minimum variance
- Risk parity
- Custom objectives based on constraints

Output Format:
- Return detailed JSON with recommendations
- Include specific trade orders (buy/sell quantities)
- Show expected improvement metrics
- Provide rationale for each recommendation
- Consider transaction costs""",

        "market-outlook": """You are a Market Outlook and Strategy Agent.

Core Responsibilities:
- Analyze macroeconomic conditions
- Research sector trends and catalysts
- Synthesize expert forecasts
- Identify opportunities and risks

Research Standards:
- Review multiple expert sources
- Cite all sources with dates
- Distinguish facts from forecasts
- Acknowledge uncertainty and ranges

Output Format:
- Return comprehensive outlook in JSON
- Include bull/base/bear scenarios
- Provide sector rotation recommendations
- List key catalysts and risks to monitor
- Include confidence levels for predictions"""
    }

    return system_prompts.get(agent_type, "You are a financial analysis agent.")


def get_execution_phases() -> dict:
    """Define the execution phases for coordinated multi-agent runs"""
    return {
        "phase_1_data_collection": {
            "agents": ["market-data"],
            "parallel": False,
            "description": "Collect market data first"
        },
        "phase_2_analysis": {
            "agents": ["portfolio-analysis", "risk-assessment", "market-outlook"],
            "parallel": True,
            "description": "Run analysis agents in parallel"
        },
        "phase_3_optimization": {
            "agents": ["optimization"],
            "parallel": False,
            "description": "Generate optimized recommendations"
        }
    }
