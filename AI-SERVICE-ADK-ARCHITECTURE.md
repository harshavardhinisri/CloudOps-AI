# CloudOps AI - Google ADK Agent Architecture (v2.0)

## Overview

The CloudOps AI service has been completely rewritten using **Google Agent Development Kit (ADK)** to implement a production-grade multi-agent incident response system. This document explains the architecture, components, and key concepts.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI REST Interface                      │
│                           (main_adk.py)                             │
└────┬──────────────────────────────────────────────────────────────┘
     │
     ├─────────────────┬──────────────────────┬──────────────────────┐
     │                 │                      │                      │
     ▼                 ▼                      ▼                      ▼
  /analyze         /remediate           /postmortem          /sessions
     │                 │                      │                      │
     └─────────────────┴──────────────────────┴──────────────────────┘
                        │
                        ▼
     ┌──────────────────────────────────────────────────┐
     │  IncidentResponseOrchestrator (Coordinator)      │
     │  - Manages multi-agent workflow                  │
     │  - Session & state management                    │
     │  - Callbacks & observability                     │
     │  - Evaluation framework                          │
     └──────────────────────────────────────────────────┘
                        │
            ┌───────────┴───────────┐
            │                       │
            ▼                       ▼
    ┌──────────────────┐    ┌──────────────────┐
    │ IncidentAnalysis │    │  Remediation     │
    │ Agent (LLM)      │    │ Agent (LLM)      │
    │                  │    │                  │
    │ Tools:           │    │ Tools:           │
    │ - query_logs     │    │ - get_remediation│
    │ - get_health     │    │ - get_health     │
    │ - analyze_logs   │    │ - validate_plan  │
    └──────────────────┘    └──────────────────┘
            │                       │
            └───────────┬───────────┘
                        │
            ┌───────────┴───────────┐
            │                       │
            ▼                       ▼
   ┌─────────────────────┐  ┌──────────────────┐
   │ Vertex AI Gemini    │  │ Tool Execution   │
   │ Flash 1.5 Model     │  │ & State Updates  │
   │ (LLM Backend)       │  │                  │
   └─────────────────────┘  └──────────────────┘
```

---

## Key Components

### 1. **Multi-Agent Architecture**

#### IncidentAnalysisAgent
- **Purpose**: Analyze incident logs and determine root cause
- **Model**: Vertex AI Gemini Flash 1.5
- **Tools**:
  - `query_logs()`: Retrieve and filter incident logs
  - `get_service_health()`: Check service health metrics
  - `analyze_incident_logs()`: Deep log pattern analysis

#### RemediationAgent
- **Purpose**: Generate and plan remediation actions
- **Model**: Vertex AI Gemini Flash 1.5
- **Tools**:
  - `get_remediation_options()`: Generate remediation plans
  - `get_service_health()`: Verify service state before/after

#### IncidentResponseOrchestrator
- **Purpose**: Coordinate agents and manage workflow
- **Responsibilities**:
  - Route incidents to appropriate agents
  - Manage sessions and state
  - Execute callbacks
  - Run evaluation framework
  - Aggregate results

---

## Crucial ADK Concepts Implemented

### 1. **LLM Agents**

```python
class IncidentAnalysisAgent(Agent):
    def __init__(self):
        tools = [
            Tool(name="query_logs", func=query_logs),
            Tool(name="get_service_health", func=get_service_health),
            ...
        ]
        config = VertexAiConfig(model="gemini-1.5-flash-001")
        super().__init__(name="incident-analyzer", tools=tools, model_config=config)
```

**Key Features**:
- Type-safe tool definitions with Python functions
- Automatic tool discovery and invocation
- Native Vertex AI Gemini integration
- Function-based tool architecture (not string-based)

---

### 2. **Session & State Management**

```python
class IncidentSession:
    def __init__(self, session_id: str, incident_context: IncidentContext):
        self.session_id = session_id
        self.state = State()  # ADK State management
        self.memory = Memory()  # ADK Memory management
        
        # Initialize state
        self.state.set("incident_id", incident_context.incident_id)
        self.state.set("status", "analyzing")
        
        # Initialize memory with context
        self.memory.add_message({
            "role": "system",
            "content": f"Analyzing incident {incident_context.incident_id}"
        })
```

**Key Features**:
- Persistent session state across agent calls
- Message memory with timestamps
- State snapshots for debugging
- Context preservation across workflows
- Session rewind capability (ADK 2.0)

---

### 3. **Memory Management**

The ADK Memory system provides:

```python
# Add to conversation memory
session.memory.add_message({
    "role": "assistant",
    "content": "Root cause identified: Connection pool exhaustion",
    "timestamp": datetime.now().isoformat()
})

# Memory features:
# - Conversation history tracking
# - Context compression (long-context optimization)
# - Context caching for cost reduction
# - Automatic message truncation for token limits
```

**Benefits**:
- Agents maintain context across multiple interactions
- Reduces token usage via caching
- Enables context compression for long conversations
- Supports conversation replay

---

### 4. **Agent Callbacks**

```python
class CloudOpsAgentCallback(AgentCallback):
    def on_event(self, event: CallbackEvent) -> None:
        """Track all agent events"""
        if event.event_type == EventType.AGENT_START:
            logger.info(f"Agent started: {event.agent.name}")
        elif event.event_type == EventType.TOOL_CALL:
            logger.info(f"Tool called: {event.tool_name}")
        elif event.event_type == EventType.TOOL_RESULT:
            logger.info(f"Tool result: {event.tool_name}")
        elif event.event_type == EventType.CONTEXT_CACHE_HIT:
            logger.info("Context cache hit - tokens saved!")
```

**Event Types**:
- `AGENT_START`: Agent begins execution
- `AGENT_END`: Agent completes
- `TOOL_CALL`: Tool invocation
- `TOOL_RESULT`: Tool execution result
- `ERROR`: Error occurred
- `CONTEXT_CACHE_HIT`: Cache hit (cost savings)
- `MEMORY_UPDATE`: Memory state changed

**Use Cases**:
- Real-time observability
- Cost tracking (cache hits)
- Debugging agent behavior
- Performance monitoring
- Audit logging

---

### 5. **Evaluation Framework**

```python
class IncidentAnalysisEvaluation:
    def __init__(self):
        self.criteria = [
            EvaluationCriteria(
                name="root_cause_accuracy",
                description="Root cause matches incident patterns",
                weight=0.4
            ),
            EvaluationCriteria(
                name="analysis_completeness",
                description="Analysis covers all affected services",
                weight=0.3
            ),
            EvaluationCriteria(
                name="remediation_feasibility",
                description="Remediation plan is executable",
                weight=0.3
            )
        ]
    
    def evaluate_analysis(self, analysis, ground_truth):
        # Compute scores against criteria
        # Return weighted overall score
        # Pass/Fail decision
```

**Evaluation Results**:
- Individual criterion scores
- Weighted overall score
- Pass/Fail determination
- Quality metrics for reporting

**Applications**:
- Quality assurance on incident analysis
- Agent performance benchmarking
- Continuous improvement tracking
- SLA compliance verification

---

### 6. **Tool Architecture**

ADK Function Tools provide automatic:
- **Type validation** via function signatures
- **Documentation** from docstrings
- **Parameter parsing** from function arguments
- **Return type handling** for structured outputs

```python
def query_logs(incident_type: str, severity: str) -> dict[str, Any]:
    """
    Query and analyze logs for incident type
    
    Args:
        incident_type: Type of incident (db_timeout, redis_unavailable, etc.)
        severity: Incident severity level
    
    Returns:
        Dict with relevant logs
    """
    # Tool implementation
    return {"status": "success", "logs": [...], "log_count": 5}
```

**Tool Features**:
- Automatic type checking
- Docstring → tool documentation
- Native Python function execution
- Error propagation
- Timeout handling

---

### 7. **Multi-Agent Workflow Orchestration**

```python
async def analyze_incident(self, incident_context: IncidentContext):
    # Step 1: Query logs
    logs_result = query_logs(...)
    
    # Step 2: Analysis agent reasoning
    analysis_result = await self._run_agent_analysis(...)
    
    # Step 3: Remediation agent planning
    remediation_result = await self._run_agent_remediation(...)
    
    # Step 4: Evaluation
    evaluation = self.evaluator.evaluate_analysis(...)
    
    # Step 5: Return orchestrated results
    return {
        "analysis": analysis_result,
        "remediation": remediation_result,
        "evaluation": evaluation
    }
```

**Orchestration Patterns**:
- Sequential agent invocation
- State passing between agents
- Parallel execution potential
- Error handling & fallbacks
- Result aggregation

---

## Workflow: Incident to Resolution

```
1. REQUEST: /api/analyze
   └─> IncidentAnalysisRequest
   
2. ORCHESTRATOR: Create Session
   └─> IncidentSession with State & Memory
   
3. ANALYSIS AGENT:
   - Tool: query_logs() → Get logs
   - Tool: get_service_health() → Check health
   - Tool: analyze_incident_logs() → Pattern detection
   - LLM: Reason about root cause
   └─> AnalysisResult
   
4. REMEDIATION AGENT:
   - Tool: get_remediation_options() → Generate plans
   - Tool: get_service_health() → Verify state
   - LLM: Plan remediation steps
   └─> RemediationPlan
   
5. EVALUATION:
   - Compare analysis against criteria
   - Compute weighted scores
   - Determine pass/fail
   └─> EvaluationResult
   
6. RESPONSE: Complete orchestrated result
   ├─> Analysis (root cause, confidence, services)
   ├─> Remediation (action, steps, rollback)
   ├─> Evaluation (scores, passed)
   └─> Session context (for future queries)
```

---

## Session & State Example

```
Session: inc-1234567890

State Tree:
├── incident_id: "inc-1234567890"
├── incident_type: "db_timeout"
├── severity: "high"
├── status: "analyzing" → "ready_for_approval" → "completed"
├── analysis:
│   ├── root_cause: "Connection pool exhaustion"
│   ├── confidence: 0.85
│   ├── affected_services: ["api-server", "worker"]
│   └── analysis_timestamp: "2026-05-27T20:15:30Z"
└── remediation:
    ├── action: "Increase pool and restart"
    ├── steps: [...]
    └── estimated_duration_minutes: 10

Memory (Conversation History):
├── system: "Analyzing incident inc-1234567890"
├── assistant: "Queried logs: 5 entries"
├── assistant: "Service health: degraded"
├── assistant: "Root cause: Connection pool exhaustion"
├── assistant: "Remediation: Increase pool size from 50 to 100"
└── system: "Evaluation score: 0.82"
```

---

## Context Caching Benefits

ADK implements automatic context caching for cost savings:

```
Without Caching:
- Every request: Full context + new input
- Cost: $0.075 per M input tokens

With ADK Caching:
- First request: Full context (cached)
- Subsequent requests: Use cached context + new input only
- Cost: $0.0094 per M cached input tokens (87.5% savings!)
- Cache hits logged via callbacks
```

---

## Error Handling & Resilience

```python
try:
    # Run agents with error handling
    analysis_result = await self._run_agent_analysis(...)
except Exception as e:
    logger.error(f"Analysis failed: {str(e)}")
    session.update_state("status", "failed")
    # Return meaningful error response
    return {
        "status": "error",
        "error_message": str(e),
        "session_context": session.get_session_context()
    }
```

---

## Deployment Architecture

### Local Development
```bash
# Install ADK
pip install -r requirements_adk.txt

# Run service
python -m uvicorn main_adk:app --reload --port 8000
```

### Cloud Run Deployment
```bash
# Build image with ADK dependencies
gcloud builds submit ./ai-service --tag=<image>

# Deploy to Cloud Run
gcloud run deploy cloudops-ai-ai-service \
  --image=<image> \
  --region=us-central1 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=<project>"
```

---

## API Endpoints

### Core Analysis
- `POST /api/analyze` - Full incident analysis with orchestration
- `POST /api/remediate` - Remediation planning
- `POST /api/remediate-execute` - Execute approved remediation
- `POST /api/postmortem` - Generate incident postmortem

### Session Management
- `GET /api/sessions` - List active sessions
- `GET /api/sessions/{id}` - Get session details
- `POST /api/evaluate/{id}` - Evaluate analysis quality

### System
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `GET /api/agents` - Agent information

---

## Extending the System

### Add New Tools

```python
def new_tool(param1: str, param2: int) -> dict:
    """Tool description"""
    return {"result": "data"}

# Register in agent
tools.append(
    adk_agent.Tool(
        name="new_tool",
        description="Tool description",
        func=new_tool
    )
)
```

### Add New Agents

```python
class CustomAgent(Agent):
    def __init__(self):
        tools = [...]
        config = VertexAiConfig(model="gemini-1.5-flash-001")
        super().__init__(name="custom", tools=tools, model_config=config)
```

### Custom Callbacks

```python
class CustomCallback(AgentCallback):
    def on_event(self, event: CallbackEvent):
        # Custom event handling
        pass
```

---

## Comparison: Old vs. New

| Aspect | Old (FastAPI + Direct LLM) | New (ADK) |
|--------|---------------------------|----------|
| **Architecture** | Simple REST API | Multi-Agent System |
| **State Management** | None | Full Session & State |
| **Memory** | None | Conversation Memory |
| **Tools** | Hardcoded functions | ADK Tool Framework |
| **Observability** | Basic logging | Callbacks + Events |
| **Evaluation** | None | Built-in Evaluation |
| **Context Caching** | None | Automatic (87.5% cost savings) |
| **Scalability** | Limited | Multi-agent Orchestration |
| **Cost** | Higher (no caching) | Lower (context caching) |
| **Production Ready** | Basic | Enterprise-grade |

---

## Key Benefits

1. **Multi-Agent Coordination**: Specialized agents for analysis and remediation
2. **State Persistence**: Sessions maintain context across interactions
3. **Memory Management**: Automatic conversation history & compression
4. **Callbacks**: Real-time observability & cost tracking
5. **Evaluation**: Quality assurance on incident analysis
6. **Context Caching**: 87.5% cost reduction on token usage
7. **Type Safety**: Python-native tool definitions
8. **Production Ready**: Enterprise patterns & best practices

---

## References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Python API Reference](https://google.github.io/adk-docs/api-reference/python/)
- [Vertex AI Gemini](https://cloud.google.com/vertex-ai/docs/generative-ai/gemini-overview)
- [ADK Agent Development Kit GitHub](https://github.com/google/adk-python)

---

## Migration Guide

To use the ADK-powered service:

1. **Update requirements.txt**:
   ```bash
   pip install -r requirements_adk.txt
   ```

2. **Update main.py** (use main_adk.py):
   ```bash
   cp main.py main_old.py
   cp main_adk.py main.py
   ```

3. **Update Dockerfile** (if using AI service):
   ```dockerfile
   COPY adk_agent.py ./adk_agent.py
   COPY main_adk.py ./main.py
   ```

4. **Rebuild & Deploy**:
   ```bash
   gcloud builds submit ./ai-service --tag=<image>
   ```

---

**Version**: 2.0.0  
**Updated**: 2026-05-27  
**Status**: Production-Ready
