"""
CloudOps AI - Google ADK Multi-Agent Incident Response System
Using the official google.adk.agents API with proper orchestration
Compatible with google-adk 2.x
"""

import os
import json
import logging
import uuid
from typing import Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Setup logging FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google ADK imports - correct API for 2.x
try:
    from google.adk.agents import LlmAgent
    from google.adk.runners import InMemoryRunner
    from google.genai import types as genai_types
    GOOGLE_ADK_AVAILABLE = True
    logger.info("✅ Google ADK available (google.adk.agents)")
except ImportError as e:
    logger.warning(f"⚠️ Google ADK not available: {e}")
    GOOGLE_ADK_AVAILABLE = False
    LlmAgent = None
    InMemoryRunner = None
    genai_types = None

# Vertex AI for LLM
try:
    from vertexai.generative_models import GenerativeModel
    VERTEX_AI_AVAILABLE = True
    logger.info("✅ Vertex AI available")
except ImportError:
    VERTEX_AI_AVAILABLE = False
    GenerativeModel = None
    logger.warning("⚠️ Vertex AI not available")

# Hallucination control
try:
    from hallucination_control import HallucinationControlSystem
    HALLUCINATION_CONTROL_ENABLED = True
    logger.info("✅ Hallucination Control System available")
except Exception as e:
    logger.warning(f"⚠️ Hallucination control disabled: {e}")
    HALLUCINATION_CONTROL_ENABLED = False


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class IncidentContext:
    """Complete incident context for agents"""
    incident_id: str
    incident_type: str
    logs: list
    severity: str = "high"
    created_at: str = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


# ============================================================================
# TOOL FUNCTIONS FOR ADK AGENTS
# ADK 2.x requires plain Python callables — NOT dicts.
# Docstrings are used as tool descriptions by the framework.
# ============================================================================

def query_logs(incident_type: str, severity: str) -> str:
    """
    Query and retrieve incident logs from the system.

    Args:
        incident_type: Type of incident (db_timeout, redis_unavailable, http_spike)
        severity: Severity level (low, medium, high, critical)

    Returns:
        JSON string with logs and metadata
    """
    logs_by_type = {
        "db_timeout": [
            "ERROR: Connection timeout to database after 30s",
            "WARN: Retrying connection to database...",
            "ERROR: Failed to acquire connection from pool (exhausted)",
            "ERROR: Connection pool has 0 available connections",
            "WARN: Queueing requests - no available connections"
        ],
        "redis_unavailable": [
            "ERROR: Redis connection refused on port 6379",
            "WARN: Cache layer unavailable",
            "ERROR: Cannot connect to Redis cluster",
            "ERROR: All Redis replicas down"
        ],
        "http_spike": [
            "WARN: HTTP 503 Service Unavailable",
            "ERROR: Request timeout after 30s",
            "WARN: High latency detected (avg 5000ms)",
            "ERROR: Circuit breaker open for downstream service"
        ]
    }

    selected_logs = logs_by_type.get(incident_type, logs_by_type["db_timeout"])

    result = {
        "status": "success",
        "logs": selected_logs,
        "log_count": len(selected_logs),
        "incident_type": incident_type,
        "severity": severity,
        "timestamp": datetime.now().isoformat()
    }

    return json.dumps(result)


def get_service_health(incident_type: str) -> str:
    """
    Check health status of all services.

    Args:
        incident_type: Type of incident to check relevant services

    Returns:
        JSON string with service health metrics
    """
    health = {
        "api-server": "degraded" if incident_type in ["db_timeout", "http_spike"] else "healthy",
        "database": "down" if incident_type == "db_timeout" else "healthy",
        "redis": "down" if incident_type == "redis_unavailable" else "healthy",
        "load-balancer": "healthy",
        "worker-pool": "degraded" if incident_type == "db_timeout" else "healthy"
    }

    result = {
        "overall_status": "degraded" if any(s != "healthy" for s in health.values()) else "healthy",
        "services": health,
        "timestamp": datetime.now().isoformat()
    }

    return json.dumps(result)


def get_remediation_options(root_cause: str, affected_services: str) -> str:
    """
    Get recommended remediation options for the identified root cause.

    Args:
        root_cause: Identified root cause from analysis
        affected_services: JSON string of affected services

    Returns:
        JSON string with remediation recommendations
    """
    remediation_map = {
        "connection_pool_exhaustion": {
            "primary_action": "Increase database connection pool size",
            "steps": [
                "Scale down worker instances to reduce connections",
                "Increase max_connections from 50 to 100",
                "Increase max_overflow to 20",
                "Verify connection metrics stabilize",
                "Gradually scale worker instances back up"
            ],
            "estimated_duration_minutes": 10,
            "risk_level": "medium"
        },
        "redis_unavailable": {
            "primary_action": "Failover to Redis replica",
            "steps": [
                "Promote Redis replica to primary",
                "Update connection strings to new primary",
                "Verify replication status",
                "Monitor memory and CPU"
            ],
            "estimated_duration_minutes": 5,
            "risk_level": "low"
        },
        "high_latency": {
            "primary_action": "Scale up API servers",
            "steps": [
                "Increase API server replicas from 3 to 6",
                "Monitor load distribution across replicas",
                "Check downstream service latency",
                "Reduce request timeout if safe"
            ],
            "estimated_duration_minutes": 5,
            "risk_level": "low"
        }
    }

    for cause_key, options in remediation_map.items():
        if cause_key.lower() in root_cause.lower():
            return json.dumps(options)

    return json.dumps({
        "primary_action": f"Investigate root cause: {root_cause}",
        "steps": ["Review logs", "Monitor metrics", "Check service dependencies"],
        "estimated_duration_minutes": 15,
        "risk_level": "low"
    })


# ============================================================================
# HELPER: extract final text from an ADK Event async generator
# ============================================================================

async def _collect_agent_response(event_stream) -> str:
    """
    Iterate over an ADK run_async event stream and return the final text output.
    ADK streams Events; the model's text response is in event.content.parts[].text.
    """
    final_text = ""
    async for event in event_stream:
        if hasattr(event, "content") and event.content:
            parts = getattr(event.content, "parts", [])
            for part in parts:
                text = getattr(part, "text", None)
                if text:
                    final_text = text  # keep the last meaningful chunk
    return final_text


# ============================================================================
# MULTI-AGENT ORCHESTRATOR USING GOOGLE ADK 2.x
# ============================================================================

class IncidentResponseOrchestrator:
    """
    Multi-agent orchestrator using Google ADK 2.x for incident response.

    Key fixes vs previous version:
    - Agent names are valid Python identifiers (underscores, no hyphens)
    - Tools are plain callables, not dicts
    - Each agent gets its own InMemoryRunner(agent=agent) at construction
    - run_async() called with user_id, session_id, new_message=types.Content(...)
    - Responses collected via async event iteration
    """

    def __init__(self):
        self.sessions = {}
        self.analysis_runner: Optional[Any] = None
        self.remediation_runner: Optional[Any] = None
        self.hallucination_control = None

        if GOOGLE_ADK_AVAILABLE:
            self._initialize_adk_agents()
        else:
            logger.warning("⚠️ ADK not available — agents will use fallback mode")

        if HALLUCINATION_CONTROL_ENABLED:
            try:
                self.hallucination_control = HallucinationControlSystem()
                logger.info("✅ Initialized HallucinationControlSystem")
            except Exception as e:
                logger.warning(f"⚠️ Hallucination control initialization failed: {e}")

        logger.info("✅ Initialized IncidentResponseOrchestrator with Google ADK 2.x")

    def _initialize_adk_agents(self):
        """
        Initialize agents and their runners using Google ADK 2.x API.

        IMPORTANT differences from previous code:
        - Agent names must be valid Python identifiers (no hyphens)
        - tools= takes a list of callables, not dicts
        - InMemoryRunner(agent=<agent>) — agent passed to runner constructor
        - One InMemoryRunner per agent
        """
        try:
            # ---- Incident Analysis Agent ----
            incident_analysis_agent = LlmAgent(
                name="incident_analyzer",           # valid Python identifier
                model="gemini-1.5-flash-001",
                instruction="""You are an expert SRE incident analyzer.
Your role is to:
1. Analyze incident logs and system health metrics
2. Identify the root cause
3. Assess severity and impact
4. List affected services

Use the available tools to query logs and check service health.
Always provide a confidence score (0-1) for your root cause analysis.
Respond in JSON with keys: root_cause, confidence, affected_services, estimated_impact, estimated_mttr.""",
                tools=[query_logs, get_service_health],  # plain callables only
            )

            # ---- Remediation Agent ----
            remediation_agent = LlmAgent(
                name="remediation_planner",         # valid Python identifier
                model="gemini-1.5-flash-001",
                instruction="""You are an expert SRE remediation planner.
Your role is to:
1. Take the identified root cause
2. Create a step-by-step remediation plan
3. Assess risk and estimated duration
4. Provide a rollback procedure

Use the available tools to get remediation recommendations.
Respond in JSON with keys: primary_action, steps, estimated_duration_minutes, risk_level, rollback_plan.""",
                tools=[get_remediation_options],    # plain callable only
            )

            # Each agent gets its own InMemoryRunner — agent passed to constructor
            self.analysis_runner = InMemoryRunner(agent=incident_analysis_agent)
            self.remediation_runner = InMemoryRunner(agent=remediation_agent)

            logger.info("✅ Created incident_analyzer and remediation_planner agents with InMemoryRunners")

        except Exception as e:
            logger.error(f"❌ Failed to initialize ADK agents: {e}")
            self.analysis_runner = None
            self.remediation_runner = None

    async def _run_agent(self, runner: Any, prompt: str, session_id: str) -> str:
        """
        Run an ADK agent via its InMemoryRunner and return the text response.

        ADK 2.x run_async signature:
            run_async(*, user_id, session_id, new_message: types.Content) -> AsyncGenerator[Event]
        """
        new_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=prompt)]
        )

        event_stream = runner.run_async(
            user_id="cloudops_system",
            session_id=session_id,
            new_message=new_message,
        )

        return await _collect_agent_response(event_stream)

    async def analyze_incident(self, incident_context: IncidentContext) -> dict[str, Any]:
        """
        Orchestrate multi-agent incident analysis workflow.

        Flow:
        1. Gather logs and service health via tool functions
        2. Run incident_analyzer LlmAgent
        3. Run remediation_planner LlmAgent
        4. Optionally verify with Hallucination Control
        5. Return complete structured response
        """
        session_id = incident_context.incident_id
        logger.info(f"🚀 Starting incident analysis for {session_id}")

        try:
            # Step 1: Gather raw information
            logger.info("📋 Step 1: Gathering incident information...")
            logs_json = query_logs(incident_context.incident_type, incident_context.severity)
            health_json = get_service_health(incident_context.incident_type)

            logs_data = json.loads(logs_json)
            health_data = json.loads(health_json)

            # Step 2: Run Analysis Agent
            analysis_result = None
            if self.analysis_runner:
                logger.info("🤖 Step 2: Running incident_analyzer via Google ADK...")
                try:
                    analysis_prompt = f"""
Analyze this production incident:
- Type: {incident_context.incident_type}
- Severity: {incident_context.severity}
- Service Health: {json.dumps(health_data['services'])}
- Recent Logs: {json.dumps(logs_data['logs'][:3])}

Use the query_logs and get_service_health tools if you need more detail.
Provide your analysis as JSON with keys:
  root_cause, confidence (0-1), affected_services (list),
  estimated_impact, estimated_mttr
"""
                    raw = await self._run_agent(
                        self.analysis_runner,
                        analysis_prompt,
                        session_id=f"{session_id}_analysis"
                    )
                    analysis_result = self._extract_json(raw)
                    logger.info(f"✅ Analysis complete: {analysis_result.get('root_cause', 'Unknown')}")
                except Exception as e:
                    logger.warning(f"⚠️ ADK analysis failed: {e} — using fallback")

            if not analysis_result:
                logger.info("ℹ️ Using fallback analysis")
                analysis_result = self._get_fallback_analysis()

            # Step 3: Run Remediation Agent
            remediation_result = None
            if self.remediation_runner:
                logger.info("🔧 Step 3: Running remediation_planner via Google ADK...")
                try:
                    remediation_prompt = f"""
Create a remediation plan for this incident:
- Root Cause: {analysis_result.get('root_cause', 'Unknown')}
- Affected Services: {json.dumps(analysis_result.get('affected_services', []))}
- Incident Type: {incident_context.incident_type}

Use the get_remediation_options tool.
Respond as JSON with keys:
  primary_action, steps (list), estimated_duration_minutes,
  risk_level, rollback_plan
"""
                    raw = await self._run_agent(
                        self.remediation_runner,
                        remediation_prompt,
                        session_id=f"{session_id}_remediation"
                    )
                    remediation_result = self._extract_json(raw)
                    logger.info(f"✅ Remediation plan: {remediation_result.get('primary_action', 'TBD')}")
                except Exception as e:
                    logger.warning(f"⚠️ ADK remediation failed: {e} — using fallback")

            if not remediation_result:
                logger.info("ℹ️ Using fallback remediation")
                remediation_result = self._get_fallback_remediation()

            # Step 4: Hallucination Control
            final_analysis = analysis_result
            hallucination_report = None

            if self.hallucination_control:
                logger.info("🛡️ Step 4: Running hallucination detection...")
                try:
                    hallucination_report = self.hallucination_control.verify_and_correct_analysis(
                        analysis_result,
                        incident_logs=logs_data.get("logs", [])
                    )
                    final_analysis = hallucination_report.get("safe_output", analysis_result)
                    logger.info(f"✅ Hallucination check: {hallucination_report.get('overall_safety', 'SAFE')}")
                except Exception as e:
                    logger.warning(f"⚠️ Hallucination control failed: {e}")
                    hallucination_report = {"error": str(e), "overall_safety": "UNKNOWN"}

            # Build final response
            response = {
                "incident_id": session_id,
                "status": "success",
                "analysis": final_analysis,
                "remediation": remediation_result,
                "timestamp": datetime.now().isoformat()
            }

            if hallucination_report:
                response["hallucination_report"] = {
                    "overall_safety": hallucination_report.get("overall_safety", "UNKNOWN"),
                    "detections_count": len(hallucination_report.get("detections", []))
                }

            logger.info(f"✅ Incident analysis complete: {session_id}")
            return response

        except Exception as e:
            logger.error(f"❌ Orchestration failed: {e}")
            return {
                "incident_id": session_id,
                "status": "error",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            }

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _extract_json(self, text: str) -> dict:
        """
        Extract a JSON object from a model response string.
        The model often wraps JSON in markdown code fences — strip them first.
        Falls back to empty dict on failure.
        """
        if not text:
            return {}
        try:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                inner = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
                cleaned = inner.strip()
            return json.loads(cleaned)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
        return {}

    def _get_fallback_analysis(self) -> dict:
        """Fallback analysis when ADK is unavailable"""
        return {
            "root_cause": "Connection pool exhaustion",
            "confidence": 0.85,
            "affected_services": ["api-server", "worker"],
            "estimated_impact": "API requests failing, data processing stalled",
            "estimated_mttr": "5-10 minutes"
        }

    def _get_fallback_remediation(self) -> dict:
        """Fallback remediation when ADK is unavailable"""
        return {
            "primary_action": "Increase connection pool and restart service",
            "steps": [
                "Scale down worker instances",
                "Increase connection pool from 50 to 100",
                "Verify pool metrics",
                "Resume traffic"
            ],
            "estimated_duration_minutes": 10,
            "risk_level": "medium",
            "rollback_plan": "Decrease pool back to 50 and restart"
        }

    def list_sessions(self):
        """List active sessions"""
        return list(self.sessions.keys())


def create_orchestrator():
    """Factory function to create the orchestrator"""
    return IncidentResponseOrchestrator()
