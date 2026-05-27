# CloudOps AI - Local Development Setup

Complete guide to run CloudOps AI locally for development and testing.

## Prerequisites

- Node.js 18+ (download from https://nodejs.org/)
- Python 3.11+ (download from https://www.python.org/)
- GCP Account with active project
- gcloud CLI installed

## Quick Start (5 minutes)

### 1. Clone/Setup Project

```bash
cd CloudOps-AI
```

### 2. Start Frontend (Terminal 1)

```bash
cd frontend
npm install
npm start
```

Frontend runs at: **http://localhost:3000**

### 3. Start Backend (Terminal 2)

```bash
cd backend
npm install
export GOOGLE_CLOUD_PROJECT=your-project-id
export AI_SERVICE_URL=http://localhost:8000
npm start
```

Backend runs at: **http://localhost:3001**

### 4. Start AI Service (Terminal 3)

```bash
cd ai-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
export GOOGLE_CLOUD_PROJECT=your-project-id
export LLM_PROVIDER=vertex_ai
python main.py
```

AI Service runs at: **http://localhost:8000**

## Full Setup with GCP Integration

### Step 1: Configure GCP Credentials

```bash
# Set your project ID
export GOOGLE_CLOUD_PROJECT=your-gcp-project-id

# Login to GCP
gcloud auth application-default login

# Enable required APIs
gcloud services enable \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com \
  logging.googleapis.com
```

### Step 2: Create Firestore Database

```bash
gcloud firestore databases create \
  --location=us-central1 \
  --type=firestore-native
```

### Step 3: Create Pub/Sub Topic

```bash
gcloud pubsub topics create incident-events
gcloud pubsub subscriptions create incident-events-sub \
  --topic=incident-events
```

### Step 4: Setup Environment Files

**backend/.env**
```
GOOGLE_CLOUD_PROJECT=your-project-id
FIRESTORE_COLLECTION=incidents
AI_SERVICE_URL=http://localhost:8000
PUBSUB_TOPIC=incident-events
PORT=3001
NODE_ENV=development
```

**ai-service/.env**
```
GOOGLE_CLOUD_PROJECT=your-project-id
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-1.5-flash-001
LLM_PROVIDER=vertex_ai
PORT=8000
```

### Step 5: Run All Services

**Terminal 1 - Frontend**
```bash
cd frontend && npm install && npm start
```

**Terminal 2 - Backend**
```bash
cd backend && npm install && \
export GOOGLE_CLOUD_PROJECT=your-project-id && \
export AI_SERVICE_URL=http://localhost:8000 && \
npm start
```

**Terminal 3 - AI Service**
```bash
cd ai-service && \
python -m venv venv && \
source venv/bin/activate && \
pip install -r requirements.txt && \
export GOOGLE_CLOUD_PROJECT=your-project-id && \
python main.py
```

## Testing the Platform

### 1. Open Frontend

Navigate to: **http://localhost:3000**

### 2. Simulate an Outage

- Click "Simulate Outage" button
- Select incident type from: db_timeout, redis_unavailable, http_spike, high_latency
- Backend creates incident with sample logs

### 3. Watch AI Analysis

- Click "Analyze" button
- AI service (using Vertex AI Gemini) analyzes logs
- Root cause and remediation are displayed

### 4. Approve Remediation

- Click "Approve & Execute" button
- Simulated remediation runs
- Timeline updates with events

### 5. View Postmortem

- After approval, click incident to view generated postmortem
- AI-generated incident report displayed

## Troubleshooting

### Frontend won't connect to backend
```bash
# Check backend is running
curl http://localhost:3001/health

# Check CORS in browser console
# Try accessing backend directly: http://localhost:3001/api/incidents
```

### Backend can't reach AI service
```bash
# Check AI service is running
curl http://localhost:8000/health

# Verify AI_SERVICE_URL environment variable
echo $AI_SERVICE_URL
```

### Firestore errors
```bash
# Verify credentials
gcloud auth list
gcloud config get-value project

# Check Firestore exists
gcloud firestore databases list

# Verify permissions
gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT
```

### Vertex AI errors
```bash
# Verify API is enabled
gcloud services list --enabled | grep aiplatform

# Test Vertex AI access
gcloud ai-platform models list
```

### Python venv issues
```bash
# Delete and recreate venv
rm -rf ai-service/venv
cd ai-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Development Tips

### Hot Reload
- Frontend: Vite supports hot reload automatically
- Backend: Use `npm run dev` for watch mode
- AI Service: Use `python -m uvicorn main:app --reload`

### Testing Endpoints

**Create incident:**
```bash
curl -X POST http://localhost:3001/api/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "type": "db_timeout",
    "severity": "high",
    "message": "Test incident",
    "logs": ["error 1", "error 2"]
  }'
```

**List incidents:**
```bash
curl http://localhost:3001/api/incidents
```

**Analyze incident:**
```bash
curl -X POST http://localhost:3001/api/incidents/INCIDENT_ID/analyze
```

### Viewing Logs

**Backend logs:**
```bash
# Check Terminal 2 output
```

**AI Service logs:**
```bash
# Check Terminal 3 output
```

**Firestore logs:**
```bash
gcloud logging read "resource.type=firestore_database" --limit 10
```

**Pub/Sub logs:**
```bash
gcloud logging read "resource.type=pubsub_topic" --limit 10
```

## Database Operations

### View Firestore Data

```bash
# List all documents
gcloud firestore documents list --collection-id=incidents

# Get specific document
gcloud firestore documents describe incidents/INCIDENT_ID

# Delete all (for cleanup)
gcloud firestore documents delete incidents/INCIDENT_ID
```

### Reset Firestore

```bash
# Delete entire collection
gcloud firestore databases delete --quiet

# Recreate
gcloud firestore databases create \
  --location=us-central1 \
  --type=firestore-native
```

## Performance Testing

### Test Frontend Performance

```bash
# Run Lighthouse audit
# In Chrome DevTools: Ctrl+Shift+P -> Lighthouse
```

### Test Backend Performance

```bash
# Install Apache Bench
# On Mac: brew install httpd
# On Ubuntu: sudo apt-get install apache2-utils

# Load test backend
ab -n 100 -c 10 http://localhost:3001/api/incidents
```

### Test AI Service Performance

```bash
# Test analysis endpoint
time curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "logs": ["error 1", "error 2"],
    "incident_type": "db_timeout"
  }'
```

## Debugging

### Enable Debug Logging

**Node.js:**
```bash
DEBUG=* npm start
```

**Python:**
```bash
export PYTHONUNBUFFERED=1
python main.py --log-level debug
```

### VS Code Debugging

**Node.js Debug Config (.vscode/launch.json):**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Backend",
      "program": "${workspaceFolder}/backend/src/server.js",
      "restart": true,
      "console": "integratedTerminal"
    }
  ]
}
```

**Python Debug Config:**
```json
{
  "type": "python",
  "request": "launch",
  "name": "AI Service",
  "program": "${workspaceFolder}/ai-service/main.py",
  "console": "integratedTerminal"
}
```

## Next Steps

1. ✓ Run all services locally
2. ✓ Test the demo workflow
3. See GCP-SETUP.md for Cloud Run deployment
4. See README.md for architecture overview

## Support

Refer to component READMEs for service-specific issues.
