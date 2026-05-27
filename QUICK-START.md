# CloudOps AI - Quick Start Guide

Get up and running with CloudOps AI in minutes.

## 30-Second Setup (Local Demo)

### Prerequisites
- Node.js 18+ and Python 3.11+
- 3 terminal windows

### Run it!

**Terminal 1 - Frontend**
```bash
cd frontend && npm install && npm start
```
Opens at: http://localhost:3000

**Terminal 2 - Backend** 
```bash
cd backend && npm install && npm start
```
Runs at: http://localhost:3001

**Terminal 3 - AI Service**
```bash
cd ai-service && python -m venv venv && \
source venv/bin/activate && \
pip install -r requirements.txt && python main.py
```
Runs at: http://localhost:8000

**Then open http://localhost:3000 and click "Simulate Outage"!**

## For GCP Deployment

1. See **GCP-SETUP.md** for complete cloud deployment
2. Run `./deploy.sh YOUR_PROJECT_ID` for automated setup
3. Access services via Cloud Run URLs

## What You Get

- **AI-Powered Incident Analysis**: Uses Vertex AI Gemini Flash to analyze logs
- **Automated Root Cause Detection**: LLM-based incident analysis
- **Remediation Recommendations**: AI-generated fix suggestions
- **Production-Ready Dashboard**: Modern React UI for incident management
- **Cloud-Native Architecture**: Serverless Cloud Run deployment

## Project Structure

```
CloudOps-AI/
├── frontend/          # React dashboard
├── backend/           # Node.js API gateway
├── ai-service/        # Python FastAPI + Vertex AI
├── deployment/        # Cloud Run configs
├── sample-data/       # Test data
├── README.md          # Full documentation
├── GCP-SETUP.md       # Cloud deployment
├── LOCAL-SETUP.md     # Local development
├── API-REFERENCE.md   # API docs
└── deploy.sh          # Auto-deployment script
```

## Features

✅ Real-time incident detection
✅ AI root cause analysis
✅ Automated remediation suggestions
✅ Incident timeline tracking
✅ Postmortem generation
✅ Firestore integration
✅ Pub/Sub event streaming
✅ Cloud Run deployment
✅ Vertex AI Gemini integration

## Key Endpoints

**Frontend**: http://localhost:3000
**Backend**: http://localhost:3001/api/incidents
**AI Service**: http://localhost:8000/api/analyze

## Demo Flow

1. Click **Simulate Outage** → Creates fake production incident
2. Click **Analyze** → AI analyzes logs with Vertex AI
3. View **Analysis Panel** → Shows root cause & confidence
4. Click **Approve & Execute** → Remediation runs
5. See **Timeline** → Full incident lifecycle

## LLM Configuration

Uses Vertex AI Gemini Flash by default (lowest cost).

Can switch to OpenRouter API by setting:
```bash
export LLM_PROVIDER=openrouter
export OPENROUTER_API_KEY=your-key
```

## Cost

- **Local**: Free
- **GCP Demo**: ~$15-50/month with Vertex AI + Cloud Run

## Documentation

- **README.md**: Full architecture & features
- **GCP-SETUP.md**: Step-by-step cloud deployment
- **LOCAL-SETUP.md**: Local development guide
- **API-REFERENCE.md**: Complete API documentation

## Troubleshooting

**Services won't start?**
```bash
# Check Node.js
node --version  # Should be 18+

# Check Python
python --version  # Should be 3.11+

# Install dependencies
cd frontend && npm install
cd ../backend && npm install
cd ../ai-service && pip install -r requirements.txt
```

**Frontend can't reach backend?**
```bash
curl http://localhost:3001/health
# Should return: {"status":"healthy"}
```

**AI service not responding?**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}
```

## Next Steps

1. ✅ Run locally to understand the workflow
2. ✅ Read GCP-SETUP.md for production deployment
3. ✅ Configure real GCP resources (Firestore, Vertex AI)
4. ✅ Connect to real production logs (optional)
5. ✅ Set up monitoring dashboards

## Support

- See README.md for full architecture
- See LOCAL-SETUP.md for development help
- See GCP-SETUP.md for deployment issues
- See API-REFERENCE.md for API details

---

**Ready to run?** Start with: `cd frontend && npm install && npm start`
