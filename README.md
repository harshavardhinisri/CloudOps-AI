# CloudOps AI - Cloud-Native SRE Platform

A production-style AI-powered incident response assistant that analyzes production logs, detects failures, identifies root causes, recommends remediation actions, and generates incident summaries.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│          (Incident Feed, Analysis, Timeline)             │
│                   Cloud Run Service                      │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API (JSON)
┌──────────────────────▼──────────────────────────────────┐
│              Node.js API Gateway                         │
│        (Express, Cloud Run Service)                      │
│  - REST Endpoints                                        │
│  - Firestore Integration                                 │
│  - Pub/Sub Publishing                                    │
└──────────────────────┬──────────────────────────────────┘
                       │ gRPC / REST
┌──────────────────────▼──────────────────────────────────┐
│          Python AI Agent Service (FastAPI)               │
│              (Cloud Run Service)                         │
│  - Google ADK Agent Architecture                         │
│  - Vertex AI Gemini Flash LLM                            │
│  - Tools: query_logs, analyze, health, remediate         │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│          GCP Services                                    │
│  - Firestore (incidents, remediation, timeline)          │
│  - Cloud Logging (log aggregation)                       │
│  - Pub/Sub (event-driven triggers)                       │
│  - Vertex AI (Gemini Flash LLM)                          │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React 18 + Tailwind CSS |
| Backend Gateway | Node.js + Express.js |
| AI Service | Python 3.11 + FastAPI |
| LLM | Vertex AI Gemini Flash |
| Database | Firestore |
| Message Queue | Pub/Sub |
| Deployment | Google Cloud Run |
| Containerization | Docker |

## Quick Start (Local Development)

### Prerequisites
- Node.js 18+
- Python 3.11+
- GCP Project configured
- gcloud CLI authenticated

### Frontend
```bash
cd frontend
npm install
npm start  # Runs on http://localhost:3000
```

### Backend
```bash
cd backend
npm install
GOOGLE_CLOUD_PROJECT=your-project \
AI_SERVICE_URL=http://localhost:8000 \
npm start  # Runs on http://localhost:3001
```

### AI Service
```bash
cd ai-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py  # Runs on http://localhost:8000
```

## Demo Flow

1. Click "Simulate Outage" in frontend
2. Backend generates incident with sample logs
3. AI service analyzes with Vertex AI Gemini Flash
4. Shows analysis and recommended remediation
5. Approve remediation to resolve incident
6. View AI-generated postmortem

## Cloud Run Deployment

See GCP-SETUP.md for complete setup instructions.

## Features

- Real-time incident detection and analysis
- AI-powered root cause identification
- Automated remediation recommendations
- Incident timeline tracking
- Postmortem generation
- Production logs analysis

## Cost Optimization

- Uses Vertex AI Gemini Flash (lowest cost)
- Batched processing
- Cached analysis results
- Configurable LLM provider

## Security

- Cloud Run services private by default
- Service-to-service authentication
- Firestore security rules
- Application Default Credentials

## Documentation

- See GCP-SETUP.md for GCP configuration
- See component READMEs in each service folder
- API documentation in API-REFERENCE.md

