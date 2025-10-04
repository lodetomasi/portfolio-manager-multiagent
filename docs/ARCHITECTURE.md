# System Architecture - Process Diagrams

## High-Level System Flow

```mermaid
graph TB
    Start([User Portfolio Input]) --> Load[Load Portfolio JSON]
    Load --> Orch[Multi-Agent Orchestrator]
    
    Orch --> Phase1[Phase 1: Data Collection]
    Phase1 --> Market[MarketDataAgent]
    Market --> WS1[WebSearch: Prices]
    Market --> WS2[WebSearch: News]
    Market --> WS3[WebSearch: Analyst Ratings]
    WS1 --> MD[Market Data JSON]
    WS2 --> MD
    WS3 --> MD
    
    MD --> Phase2[Phase 2: Parallel Analysis]
    
    Phase2 --> PA[PortfolioAgent]
    Phase2 --> RA[RiskAgent]
    
    PA --> Calc1[Calculate Metrics]
    Calc1 --> Sharpe[Sharpe Ratio]
    Calc1 --> Vol[Volatility]
    Calc1 --> Corr[Correlations]
    Sharpe --> PM[Portfolio Metrics]
    Vol --> PM
    Corr --> PM
    
    RA --> Risk1[Risk Calculations]
    Risk1 --> VaR[VaR 95%]
    Risk1 --> CVaR[CVaR]
    Risk1 --> Stress[Stress Tests]
    VaR --> RM[Risk Metrics]
    CVaR --> RM
    Stress --> RM
    
    PM --> Phase3[Phase 3: Optimization]
    RM --> Phase3
    
    Phase3 --> OA[OptimizationAgent]
    OA --> EF[Efficient Frontier]
    EF --> Optimal[Optimal Allocation]
    Optimal --> Trades[Trade Orders]
    
    Trades --> Report[JSON Report]
    Report --> End([Complete Analysis])
    
    style Phase2 fill:#f9f,stroke:#333,stroke-width:3px
    style PA fill:#bbf,stroke:#333,stroke-width:2px
    style RA fill:#bbf,stroke:#333,stroke-width:2px
```

## Detailed Agent Execution Flow

```mermaid
flowchart TD
    subgraph Init[Initialization]
        I1[Parse CLI Arguments]
        I2[Load Portfolio JSON]
        I3[Validate Holdings]
        I4[Create Orchestrator]
        I1 --> I2 --> I3 --> I4
    end
    
    subgraph Phase1[Phase 1: Market Data]
        M1[Create MarketDataAgent]
        M2[Build Query Prompt]
        M3[Set allowed_tools: WebSearch, WebFetch]
        M4[Execute query with SDK]
        M5{Message Type?}
        M6[Skip SystemMessage]
        M7[Extract TextBlock]
        M8[Parse JSON]
        M9[Market Data Ready]
        
        M1 --> M2 --> M3 --> M4 --> M5
        M5 -->|System| M6 --> M4
        M5 -->|Assistant/Result| M7 --> M8 --> M9
    end
    
    subgraph Phase2[Phase 2: Parallel Analysis]
        direction TB
        
        subgraph Portfolio[PortfolioAgent Task]
            P1[Create Task]
            P2[System Prompt: MPT Expert]
            P3[allowed_tools: Bash]
            P4[Calculate Weights]
            P5[Compute Sharpe]
            P6[Correlation Matrix]
            P7[Return Metrics]
            P1 --> P2 --> P3 --> P4 --> P5 --> P6 --> P7
        end
        
        subgraph Risk[RiskAgent Task]
            R1[Create Task]
            R2[System Prompt: Risk Expert]
            R3[allowed_tools: Bash, WebSearch]
            R4[Calculate VaR/CVaR]
            R5[Run Stress Tests]
            R6[Concentration Analysis]
            R7[Return Risk Metrics]
            R1 --> R2 --> R3 --> R4 --> R5 --> R6 --> R7
        end
        
        Sync[asyncio.gather]
        Portfolio --> Sync
        Risk --> Sync
        Sync --> Combined[Combined Results]
    end
    
    subgraph Phase3[Phase 3: Optimization]
        O1[Create OptimizationAgent]
        O2[System Prompt: Optimizer]
        O3[allowed_tools: Bash]
        O4[Define Constraints]
        O5[Compute Efficient Frontier]
        O6[Find Optimal Weights]
        O7[Generate Trades]
        O8[Calculate Improvement]
        
        O1 --> O2 --> O3 --> O4 --> O5 --> O6 --> O7 --> O8
    end
    
    subgraph Output[Report Generation]
        Rep1[Consolidate Results]
        Rep2[Generate Summary]
        Rep3[Create Action Items]
        Rep4[Save JSON Report]
        Rep5[Display to User]
        
        Rep1 --> Rep2 --> Rep3 --> Rep4 --> Rep5
    end
    
    Init --> Phase1 --> Phase2 --> Phase3 --> Output
```

## Agent Message Processing Pipeline

```mermaid
stateDiagram-v2
    [*] --> AgentQuery: Call query()
    
    AgentQuery --> StreamMessages: Async iteration
    
    StreamMessages --> CheckMessageType: Receive message
    
    CheckMessageType --> SystemMessage: type = SystemMessage
    CheckMessageType --> AssistantMessage: type = AssistantMessage
    CheckMessageType --> UserMessage: type = UserMessage
    CheckMessageType --> ResultMessage: type = ResultMessage
    
    SystemMessage --> Skip: Skip (metadata only)
    Skip --> StreamMessages
    
    AssistantMessage --> ExtractContent: Get message.result
    UserMessage --> ExtractContent
    ResultMessage --> ExtractContent
    
    ExtractContent --> CheckBlocks: isinstance(content, list)?
    
    CheckBlocks --> IterateBlocks: Yes
    CheckBlocks --> DirectString: No
    
    IterateBlocks --> TextBlock: hasattr(block, 'text')
    IterateBlocks --> ToolUseBlock: hasattr(block, 'name')
    
    TextBlock --> AccumulateText: Append block.text
    ToolUseBlock --> SkipToolUse: Skip function calls
    
    AccumulateText --> StreamMessages
    SkipToolUse --> StreamMessages
    DirectString --> AccumulateText
    
    StreamMessages --> Complete: Stream ended
    Complete --> ParseJSON: Extract ```json blocks
    ParseJSON --> [*]: Return structured data
```

## Data Flow Through System

```mermaid
graph LR
    subgraph Input
        PJ[Portfolio JSON]
        Obj[Optimization Objective]
    end
    
    subgraph MarketData
        WS[Web Search Results]
        Prices[Real-time Prices]
        News[Market News]
        Ratings[Analyst Ratings]
    end
    
    subgraph Analytics
        Metrics[Portfolio Metrics]
        RiskData[Risk Assessment]
        Optimized[Optimal Allocation]
    end
    
    subgraph Output
        Report[JSON Report]
        Trades[Trade Orders]
        Summary[Executive Summary]
    end
    
    PJ --> MarketData
    Obj --> Analytics
    
    WS --> Prices
    WS --> News
    WS --> Ratings
    
    Prices --> Metrics
    Prices --> RiskData
    
    Metrics --> Optimized
    RiskData --> Optimized
    
    Optimized --> Trades
    Metrics --> Report
    RiskData --> Report
    Optimized --> Report
    
    Report --> Summary
    Trades --> Summary
```

## Parallel Execution Timeline

```mermaid
gantt
    title Multi-Agent Analysis Timeline
    dateFormat X
    axisFormat %L
    
    section Phase 1
    Load Portfolio         :p1, 0, 5
    MarketDataAgent       :p2, 5, 50
    
    section Phase 2 (Parallel)
    PortfolioAgent        :p3, 55, 35
    RiskAgent             :p4, 55, 40
    
    section Phase 3
    Wait for Phase 2      :p5, 95, 1
    OptimizationAgent     :p6, 96, 30
    
    section Reporting
    Generate Report       :p7, 126, 10
    Display Results       :p8, 136, 5
```

## Error Handling Flow

```mermaid
graph TD
    Start[Agent Execution] --> Try{Try Block}
    
    Try -->|Success| Process[Process Messages]
    Try -->|Timeout| TO[asyncio.TimeoutError]
    Try -->|JSON Error| JE[JSONDecodeError]
    Try -->|Other| GE[General Exception]
    
    Process --> Parse{Parse JSON}
    Parse -->|Success| Return[Return Data]
    Parse -->|Fail| JE
    
    TO --> Partial[Return Partial Data]
    JE --> Fallback[Return Raw + Error]
    GE --> Log[Log Exception]
    
    Partial --> End[Continue Execution]
    Fallback --> End
    Log --> End
    Return --> End
    
    End --> Next[Next Agent/Phase]
```

## SDK Integration Architecture

```mermaid
C4Context
    title System Context - Claude Agent SDK Integration
    
    Person(user, "Portfolio Manager", "Uses system for analysis")
    
    System_Boundary(sys, "Multi-Agent System") {
        Container(orch, "Orchestrator", "Python asyncio", "Coordinates agents")
        Container(market, "MarketDataAgent", "Claude SDK", "Real-time data")
        Container(port, "PortfolioAgent", "Claude SDK", "MPT analysis")
        Container(risk, "RiskAgent", "Claude SDK", "Risk metrics")
        Container(opt, "OptimizationAgent", "Claude SDK", "Optimization")
    }
    
    System_Ext(claude, "Claude Code", "Claude Agent SDK", "AI execution engine")
    System_Ext(web, "Web Sources", "Financial data providers")
    
    Rel(user, orch, "Provides portfolio")
    Rel(orch, market, "Delegates data collection")
    Rel(orch, port, "Delegates analysis", "parallel")
    Rel(orch, risk, "Delegates risk", "parallel")
    Rel(orch, opt, "Delegates optimization")
    
    Rel(market, claude, "query() with WebSearch")
    Rel(port, claude, "query() with Bash")
    Rel(risk, claude, "query() with Bash+Web")
    Rel(opt, claude, "query() with Bash")
    
    Rel(claude, web, "Fetches market data")
```

## Key Design Patterns

### 1. Agent Specialization
Each agent has:
- Dedicated `system_prompt` defining expertise
- Constrained `allowed_tools` for security
- Specific output schema

### 2. Parallel Execution
```python
# Phase 2: Portfolio and Risk run simultaneously
portfolio_task = asyncio.create_task(portfolio_agent.analyze(...))
risk_task = asyncio.create_task(risk_agent.assess(...))

# Wait for both to complete
results = await asyncio.gather(portfolio_task, risk_task)
```

### 3. Message Filtering
```python
for message in query(...):
    if 'System' in type(message).__name__:
        continue  # Skip metadata
    
    if isinstance(content, list):
        for block in content:
            if hasattr(block, 'text'):
                accumulate(block.text)
```

### 4. Timeout Safety
```python
async with asyncio.timeout(120):  # 2-minute max
    async for message in query(...):
        process(message)
```

## Performance Characteristics

- **Sequential Execution:** ~150s total
- **With Parallel Phase 2:** ~90s total
- **Speedup:** 1.67x
- **Bottleneck:** Market data collection (synchronous web searches)

## Future Enhancements

1. **Phase 1 Parallelization**: Split market data by symbol
2. **Caching Layer**: Cache market data for repeated analyses
3. **Streaming UI**: Real-time progress updates
4. **MCP Integration**: Custom financial data tools
