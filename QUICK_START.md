# CloudOps AI - Quick Start Guide

## 5-Minute Setup & Testing

### Prerequisites
You should have already completed:
- ✅ Python 3.11+ installed
- ✅ Google Cloud SDK installed (`gcloud`)
- ✅ Project cloned to `/Users/harsha/CloudOps-AI`

---

## Step 1: Create Python Virtual Environment (1 minute)

```bash
cd /Users/harsha/CloudOps-AI/ai-service

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Verify activation (should show "venv" in prompt)
which python
```

---

## Step 2: Install Dependencies (2 minutes)

```bash
# Make sure you're in ai-service directory with venv activated
pip install -r requirements.txt

# Verify Google ADK installed correctly
python3 -c "from google.adk.agents import Agent; print('✅ Google ADK ready')"
```

---

## Step 3: Run Local Tests (1 minute)

```bash
# Make test script executable
chmod +x test_adk_locally.py

# Run comprehensive tests
python3 test_adk_locally.py
```

**Expected Output:**
```
======================================================================
  CloudOps AI - Local ADK Testing Suite
  Google ADK Multi-Agent Incident Response System
======================================================================

======================================================================
  Testing Critical Imports
======================================================================
✅ FastAPI imported
✅ Pydantic imported
✅ google.adk.agents.Agent imported
✅ google.adk.runners.InMemoryRunner imported
✅ vertexai.generative_models.GenerativeModel imported
✅ HallucinationControlSystem imported

... (more tests) ...

======================================================================
  Test Summary
======================================================================
Total Tests Passed: 12
Total Tests Failed: 0

🎉 All tests passed! Ready for Cloud Run deployment! 🎉
```

---

## Step 4: Start Service Locally (Optional - 30 seconds)

```bash
# In the ai-service directory with venv activated
python3 main.py

# Output should show:
# INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

In another terminal, test the service:
```bash
# Test health check
curl http://localhost:8080/health

# Should return:
# {"status":"healthy","service":"CloudOps AI ADK Agent Service",...}
```

---

## Step 5: Deploy to Cloud Run (3 minutes)

### Set up Google Cloud credentials:
```bash
gcloud auth login
gcloud config set project possible-point-497521-g1
gcloud auth configure-docker gcr.io
```

### Build and Deploy:
```bash
cd /Users/harsha/CloudOps-AI

# Build Docker image (runs in Google Cloud - handles cross-platform builds)
gcloud builds submit ./ai-service \
  --tag=gcr.io/possible-point-497521-g1/cloudops-ai-ai-service

# Deploy to Cloud Run
gcloud run deploy cloudops-ai-ai-service \
  --image=gcr.io/possible-point-497521-g1/cloudops-ai-ai-service \
  --region=us-central1 \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=possible-point-497521-g1 \
  --allow-unauthenticated \
  --timeout=60 \
  --memory=2Gi \
  --cpu=2
```

**Output will show:**
```
Service deployed at: https://cloudops-ai-ai-service-XXXXXXXXX.us-central1.run.app
```

Copy that URL - you'll need it next.

---

## Step 6: Test Cloud Deployment (2 minutes)

```bash
cd /Users/harsha/CloudOps-AI/ai-service

# Make curl test script executable
chmod +x test_with_curl.sh

# Test against Cloud Run
./test_with_curl.sh cloud

# When prompted, paste the Cloud Run URL:
# https://cloudops-ai-ai-service-XXXXXXXXX.us-central1.run.app
```

**You should see:**
```
========================================================
TEST: Health Check
========================================================
✅ Health check passed (HTTP 200)

========================================================
TEST: Readiness Check
========================================================
✅ Readiness check passed (HTTP 200)

... (more tests) ...

🎉 All tests passed!
```

---

## Step 7: Integrate with Frontend (1 minute)

Update your React frontend to use the Cloud Run URL:

**File: `/Users/harsha/CloudOps-AI/frontend/src/App.jsx`**

Find this line (around line 18):
```javascript
const getApiUrl = () => {
```

Make sure it constructs the backend URL correctly. It should replace "cloudops-ai-frontend" with "cloudops-ai-backend" in the hostname.

Or manually set the environment variable:
```bash
# In frontend Cloud Run deployment
--set-env-vars=REACT_APP_API_URL=https://cloudops-ai-ai-service-XXXXXXXXX.us-central1.run.app
```

---

## What Each Test Verifies

### Local Test Script (`test_adk_locally.py`)
✅ Google ADK imports working  
✅ Tool functions callable  
✅ Agents created successfully  
✅ InMemoryRunner working  
✅ Orchestrator can run multi-agent workflow  
✅ Hallucination control integrated  
✅ FastAPI endpoints respond  
✅ Full incident analysis works  

### Curl Test Script (`test_with_curl.sh`)
✅ Health check responds  
✅ Readiness probe works  
✅ Service info available  
✅ Analysis endpoint receives requests  
✅ Root cause identified  
✅ Remediation plan generated  
✅ Hallucination report included  
✅ Session listing works  

---

## Verifying Google ADK Integration

When the service starts, you should see these log messages:

```
✅ Google ADK available (google.adk.agents)
✅ Vertex AI available
✅ Created IncidentAnalysisAgent
✅ Created RemediationAgent
✅ Initialized InMemoryRunner for agent execution
✅ Initialized IncidentResponseOrchestrator with Google ADK
```

When you call `/api/analyze`:

```
🚀 Starting incident analysis for inc-001
📋 Step 1: Gathering incident information...
🤖 Step 2: Running IncidentAnalysisAgent via Google ADK...
✅ Analysis complete: Connection pool exhaustion
🔧 Step 3: Running RemediationAgent via Google ADK...
✅ Remediation plan created: Increase connection pool...
🛡️ Step 4: Running hallucination detection...
✅ Hallucination check: SAFE
✅ Incident analysis complete: inc-001
```

---

## Troubleshooting

### Problem: "Google ADK not available"
```bash
# Check if google-adk is installed
pip list | grep google-adk

# If not, install it
pip install google-adk
```

### Problem: "Connection refused" when testing locally
```bash
# Make sure service is running in another terminal
python3 main.py

# And make sure you're testing against http://localhost:8080
curl http://localhost:8080/health
```

### Problem: Cloud Run deployment fails
```bash
# Check Cloud Build logs
gcloud builds log --stream

# Check Cloud Run logs
gcloud run logs read cloudops-ai-ai-service --region=us-central1 --limit=50

# Increase timeout and memory if needed
gcloud run deploy cloudops-ai-ai-service \
  --image=gcr.io/possible-point-497521-g1/cloudops-ai-ai-service \
  --region=us-central1 \
  --timeout=120 \
  --memory=4Gi \
  --cpu=4
```

### Problem: "Container manifest type must support amd64/linux"
✅ **Already fixed!** We use `gcloud builds submit` which handles cross-platform builds automatically.

---

## Performance Expectations

- **Service Startup**: 10-20 seconds
- **Health Check**: <100ms
- **Incident Analysis**: 5-10 seconds (includes Vertex AI API call)
- **Full Response**: 10-15 seconds (analysis + remediation + safety check)

---

## What's Running

After deployment, you have these services on Google Cloud Run:

1. **cloudops-ai-frontend** - React dashboard
2. **cloudops-ai-backend** - Node.js API gateway
3. **cloudops-ai-ai-service** - Python ADK AI service (just deployed)

All communicate via HTTPS with Cloud Run URLs.

---

## Next Steps

1. ✅ **Complete**: Local testing passes
2. ✅ **Complete**: Cloud Run deployment working
3. **Now**: Test full end-to-end workflow through React dashboard
4. **Then**: Monitor Cloud Logging for production incidents
5. **Finally**: Integrate with your monitoring tools (alerts → CloudOps AI)

---

## Key URLs After Deployment

Replace `XXXXXXXXX` with your actual service IDs:

```
Frontend:  https://cloudops-ai-frontend-XXXXXXXXX.us-central1.run.app
Backend:   https://cloudops-ai-backend-XXXXXXXXX.us-central1.run.app
AI Service: https://cloudops-ai-ai-service-XXXXXXXXX.us-central1.run.app
```

Test AI Service directly:
```bash
curl https://cloudops-ai-ai-service-XXXXXXXXX.us-central1.run.app/health
```

---

## Architecture Overview

```
┌──────────────────┐
│   React UI       │
│ (Incident Mgmt)  │
└────────┬─────────┘
         │ REST API
         ▼
┌──────────────────┐
│  Node.js Backend │
│  (API Gateway)   │
└────────┬─────────┘
         │ REST API
         ▼
┌──────────────────────────────────┐
│  Python ADK AI Service           │
│  ├─ IncidentAnalysisAgent        │
│  ├─ RemediationAgent             │
│  ├─ HallucinationControlSystem   │
│  └─ Tool Binding                 │
└────────┬─────────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────────┐
│Vertex  │ │Hallucination │
│ AI     │ │Control Sys   │
│Gemini  │ │(6 techniques)│
└────────┘ └──────────────┘
```

---

## You're All Set! 🎉

The Google ADK integration is complete and your CloudOps AI platform is ready for production use.

**Total Setup Time**: ~15 minutes  
**Status**: Production-ready
**Next**: Deploy and test!

For detailed documentation, see:
- `DEPLOY_AND_TEST.md` - Comprehensive deployment guide
- `GOOGLE_ADK_INTEGRATION_COMPLETE.md` - Technical details
