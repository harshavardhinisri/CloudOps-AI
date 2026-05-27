# CloudOps AI - Local Development Setup

## Prerequisites
- Python 3.10+ 
- pip3
- Virtual environment support

## Step 1: Create Virtual Environment (Recommended)

```bash
cd ai-service
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate  # On Windows
```

## Step 2: Install Dependencies

```bash
pip3 install -r requirements_adk.txt
```

## Step 3: Set Environment Variables

Create `.env` file in ai-service directory:

```bash
cat > .env << EOF
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
EOF
```

Or set them directly:

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
```

## Step 4: Run the Service Locally

**Option A: Development Mode (with auto-reload)**
```bash
python3 -m uvicorn main:app --reload --port 8000
```

**Option B: Production Mode**
```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Step 5: Test the API

In a new terminal:

```bash
# Health check
curl http://localhost:8000/health

# Readiness check (includes hallucination control status)
curl http://localhost:8000/ready

# Test incident analysis
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "logs": [
      "ERROR: Connection timeout to database",
      "WARN: Retrying connection...",
      "ERROR: Failed to acquire connection from pool"
    ],
    "incident_type": "db_timeout",
    "severity": "high"
  }' | python3 -m json.tool
```

## Expected Response

```json
{
  "incident_id": "inc-1234567890.123456",
  "status": "success",
  "analysis": {
    "root_cause": "Connection pool exhaustion",
    "confidence": 0.85,
    "affected_services": ["api-server", "worker"],
    "estimated_impact": "API requests failing, data processing stalled",
    "estimated_mttr": "5-10 minutes"
  },
  "remediation": {
    "action": "Increase pool size and restart service",
    "severity": "high",
    "steps": [...]
  },
  "evaluation": {
    "overall_score": 0.82,
    "passed": true
  },
  "hallucination_report": {
    "overall_safety": "SAFE",
    "detections_count": 2,
    "corrections_applied": []
  },
  "timestamp": "2026-05-27T..."
}
```

## Troubleshooting

### Module Not Found: google.adk
```bash
# Verify installation
python3 -c "import google.adk; print('ADK installed')"

# If missing, reinstall
pip3 install --upgrade google-adk google-cloud-aiplatform vertexai
```

### Vertex AI Not Configured
```bash
# Set credentials
export GOOGLE_CLOUD_PROJECT=your-project
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Verify
gcloud auth application-default login
```

### Hallucination Control Not Found
This is non-fatal. The service will log a warning and run without safety checks.

### Port 8000 Already in Use
```bash
# Use a different port
python3 -m uvicorn main:app --reload --port 8001
```

## Architecture

The integrated system includes:

1. **Multi-Agent Orchestration** (adk_agent.py)
   - IncidentAnalysisAgent: Root cause analysis
   - RemediationAgent: Remediation planning

2. **Hallucination Control** (hallucination_control.py)
   - Detects 6 types of hallucinations
   - Validates against ground truth database
   - Applies corrections before returning results

3. **REST API** (main.py)
   - POST /api/analyze: Full analysis with safety checks
   - GET /health: Service health
   - GET /ready: Readiness status (shows hallucination control enabled)

## Integration Flow

```
Request
  ↓
[IncidentAnalysisAgent] → Analysis Result
  ↓
[RemediationAgent] → Remediation Plan
  ↓
[Evaluation] → Quality Score
  ↓
[HallucinationControlSystem] ← NEW
  ├─ HallucinationDetector: Find issues
  ├─ OutputValidator: Validate schema
  └─ VerificationAgent: Cross-check
  ↓
Safe Result
  ↓
Response with hallucination_report
```

## Next Steps

1. Test locally to verify hallucination control integration
2. Deploy to Cloud Run: `gcloud run deploy cloudops-ai-ai-service --source ai-service`
3. Monitor hallucination reports in production
4. Iterate on ground truth database based on real incidents
