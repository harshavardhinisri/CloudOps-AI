import os
import json
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import uvicorn

from tools.log_analyzer import analyze_logs
from tools.incident_analyzer import analyze_incident
from tools.service_health import get_service_health
from tools.remediation import generate_remediation, execute_remediation
from utils.llm import get_llm_response
from utils.sample_logs import get_sample_logs_for_type

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="CloudOps AI - AI Agent Service",
    version="1.0.0",
    description="AI-powered incident response agent using Vertex AI Gemini"
)

# Request/Response Models
class AnalyzeRequest(BaseModel):
    logs: List[str]
    incident_type: str

class AnalyzeResponse(BaseModel):
    root_cause: str
    confidence: float
    affected_services: List[str]
    estimated_impact: str
    estimated_mttr: str

class RemediateRequest(BaseModel):
    incident_id: str
    root_cause: str
    service: str

class RemediateResponse(BaseModel):
    action: str
    severity: str
    steps: List[str]

class RemediateExecuteRequest(BaseModel):
    incident_id: str
    action: str

class RemediateExecuteResponse(BaseModel):
    status: str
    message: str
    execution_time: float

class PostmortemRequest(BaseModel):
    incident_id: str
    root_cause: str
    remediation: str
    duration_minutes: int

class PostmortemResponse(BaseModel):
    postmortem: str

# Health Check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "cloudops-ai-ai-service",
        "timestamp": "2026-05-27T00:00:00Z"
    }

# Analyze Logs Endpoint
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    Analyze production logs to identify issues
    """
    try:
        logger.info(f"Analyzing {len(request.logs)} logs for incident type: {request.incident_type}")
        
        # Run log analysis
        analysis_results = analyze_logs(request.logs, request.incident_type)
        
        # Use LLM to generate detailed root cause
        prompt = f"""Analyze this incident and provide the root cause:
        
Incident Type: {request.incident_type}
Logs: {json.dumps(request.logs[:5])}
Initial Analysis: {analysis_results['summary']}

Provide a brief, technical root cause explanation."""
        
        root_cause = get_llm_response(prompt)
        
        return AnalyzeResponse(
            root_cause=root_cause or analysis_results['summary'],
            confidence=analysis_results['confidence'],
            affected_services=analysis_results['affected_services'],
            estimated_impact=analysis_results['estimated_impact'],
            estimated_mttr=analysis_results['estimated_mttr']
        )
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Generate Remediation Endpoint
@app.post("/api/remediate", response_model=RemediateResponse)
async def remediate(request: RemediateRequest):
    """
    Generate remediation steps for an incident
    """
    try:
        logger.info(f"Generating remediation for incident {request.incident_id}")
        
        # Get service health
        health = get_service_health(request.service)
        
        # Generate remediation with LLM
        prompt = f"""Based on this incident, suggest remediation steps:

Incident ID: {request.incident_id}
Service: {request.service}
Root Cause: {request.root_cause}
Current Health: {health}

Provide specific, actionable remediation steps in a numbered list."""
        
        remediation_text = get_llm_response(prompt)
        
        # Parse remediation steps
        steps = [
            step.strip() 
            for step in remediation_text.split('\n') 
            if step.strip() and not step.startswith('#')
        ][:3]  # Limit to 3 steps
        
        action = steps[0] if steps else "Investigate incident and restart service"
        
        return RemediateResponse(
            action=action,
            severity="high" if "critical" in request.root_cause.lower() else "medium",
            steps=steps or ["Monitor metrics", "Check logs", "Restart service if needed"]
        )
    except Exception as e:
        logger.error(f"Remediation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Remediation failed: {str(e)}")

# Execute Remediation Endpoint
@app.post("/api/remediate-execute", response_model=RemediateExecuteResponse)
async def execute_remediation_action(request: RemediateExecuteRequest):
    """
    Execute remediation action (simulated)
    """
    try:
        logger.info(f"Executing remediation for incident {request.incident_id}")
        
        # Simulate execution
        result = execute_remediation(request.action)
        
        return RemediateExecuteResponse(
            status="executed",
            message=f"Remediation executed: {result}",
            execution_time=2.5
        )
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

# Generate Postmortem Endpoint
@app.post("/api/postmortem", response_model=PostmortemResponse)
async def generate_postmortem(request: PostmortemRequest):
    """
    Generate AI-powered incident postmortem
    """
    try:
        logger.info(f"Generating postmortem for incident {request.incident_id}")
        
        prompt = f"""Generate a professional incident postmortem report:

Incident ID: {request.incident_id}
Duration: {request.duration_minutes} minutes
Root Cause: {request.root_cause}
Remediation: {request.remediation}

Include: Executive summary, impact analysis, timeline, root cause analysis, remediation steps, and preventive measures."""
        
        postmortem = get_llm_response(prompt)
        
        return PostmortemResponse(
            postmortem=postmortem or f"""Incident Postmortem Report
{request.incident_id}

Timeline:
- Incident detected and analyzed
- Root cause identified: {request.root_cause}
- Remediation applied: {request.remediation}
- Service recovered after {request.duration_minutes} minutes

Impact: Limited impact due to rapid response

Prevention: Implement better monitoring and alerting"""
        )
    except Exception as e:
        logger.error(f"Postmortem generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Postmortem generation failed: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "CloudOps AI - AI Agent Service",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/api/analyze": "Analyze logs and identify issues",
            "/api/remediate": "Generate remediation steps",
            "/api/remediate-execute": "Execute remediation",
            "/api/postmortem": "Generate incident postmortem"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"\n✓ Starting AI Service on http://0.0.0.0:{port}")
    print(f"✓ Project: {os.getenv('GOOGLE_CLOUD_PROJECT', 'not-set')}")
    print(f"✓ LLM Provider: {os.getenv('LLM_PROVIDER', 'vertex_ai')}\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
