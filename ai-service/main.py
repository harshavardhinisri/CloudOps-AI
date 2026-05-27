"""
CloudOps AI - FastAPI REST Interface for ADK Agent Service with Hallucination Control
"""

import os
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from adk_agent import (
    create_orchestrator,
    IncidentContext,
    HALLUCINATION_CONTROL_ENABLED,
    VERTEX_AI_AVAILABLE
)

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="CloudOps AI - ADK-powered Agent Service with Hallucination Control",
    version="2.0.0",
    description="AI-powered incident response using Vertex AI Gemini + Hallucination Control"
)

# Initialize orchestrator
try:
    orchestrator = create_orchestrator()
    logger.info("✅ Orchestrator initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize orchestrator: {e}")
    orchestrator = None


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Incident analysis request"""
    logs: List[str]
    incident_type: str
    severity: str = "high"
    incident_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    timestamp: str


class ReadyResponse(BaseModel):
    """Readiness check response"""
    status: str
    orchestrator_available: bool
    vertex_ai_available: bool
    hallucination_control_enabled: bool
    timestamp: str


# ============================================================================
# HEALTH & READINESS ENDPOINTS
# ============================================================================

@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CloudOps AI ADK Agent Service",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/ready", response_model=dict)
async def readiness_check():
    """Readiness check - verifies orchestrator is initialized"""
    return {
        "status": "ready" if orchestrator else "not_ready",
        "orchestrator_available": orchestrator is not None,
        "vertex_ai_available": VERTEX_AI_AVAILABLE,
        "hallucination_control_enabled": HALLUCINATION_CONTROL_ENABLED,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.post("/api/analyze", response_model=dict)
async def analyze(request: AnalyzeRequest):
    """
    Analyze incident using ADK-based orchestrator with hallucination control

    Workflow:
    1. Query logs and check service health
    2. Run incident analysis (LLM + ADK concepts)
    3. Generate remediation plan
    4. Verify for hallucinations (safety layer)
    5. Return complete analysis with safety report
    """
    if not orchestrator:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "error_message": "Orchestrator not initialized"}
        )

    try:
        logger.info(f"📊 Received analysis request for {request.incident_type}")

        # Create incident context
        incident_context = IncidentContext(
            incident_id=request.incident_id or f"inc-{datetime.now().timestamp()}",
            incident_type=request.incident_type,
            logs=request.logs,
            severity=request.severity
        )

        # Run orchestrator workflow
        result = await orchestrator.analyze_incident(incident_context)

        if result["status"] == "success":
            logger.info(f"✅ Analysis completed for incident {incident_context.incident_id}")
            return JSONResponse(status_code=200, content=result)
        else:
            logger.error(f"Analysis failed: {result.get('error_message')}")
            return JSONResponse(status_code=500, content=result)

    except Exception as e:
        logger.error(f"❌ Error in analyze endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.get("/api/sessions")
async def list_sessions():
    """List active sessions"""
    if not orchestrator:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "error_message": "Orchestrator not initialized"}
        )

    return {
        "sessions": orchestrator.list_sessions(),
        "count": len(orchestrator.list_sessions()),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/info")
async def service_info():
    """Service information"""
    return {
        "service": "CloudOps AI ADK Agent Service",
        "version": "2.0.0",
        "features": {
            "incident_analysis": True,
            "hallucination_control": HALLUCINATION_CONTROL_ENABLED,
            "vertex_ai_integration": VERTEX_AI_AVAILABLE,
            "adk_orchestration": True
        },
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
