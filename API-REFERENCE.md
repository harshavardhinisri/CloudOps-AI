# CloudOps AI - API Reference

Complete API documentation for CloudOps AI services.

## Backend Service (Node.js)

Base URL: `http://localhost:3001` (local) or `https://cloudops-ai-backend.run.app` (Cloud Run)

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-27T12:00:00Z"
}
```

### Get All Incidents

**Endpoint:** `GET /api/incidents`

**Query Parameters:**
- `status` (optional): Filter by status (open, resolved)
- `severity` (optional): Filter by severity (low, medium, high, critical)
- `limit` (optional): Max results to return (default: 100)

**Response:**
```json
[
  {
    "id": "uuid",
    "type": "db_timeout",
    "severity": "high",
    "message": "Database connection timeout",
    "status": "open",
    "created_at": "2026-05-27T12:00:00Z",
    "analysis": {...},
    "recommended_action": "...",
    "timeline": [...]
  }
]
```

### Get Specific Incident

**Endpoint:** `GET /api/incidents/:id`

**Response:**
```json
{
  "id": "incident-uuid",
  "type": "db_timeout",
  "severity": "high",
  "message": "Database connection timeout detected",
  "logs": ["error 1", "error 2"],
  "status": "open",
  "created_at": "2026-05-27T12:00:00Z",
  "analysis": {
    "root_cause": "Connection pool exhausted",
    "confidence": 0.92,
    "affected_services": ["api-server", "worker"],
    "estimated_impact": "High - 500 users",
    "estimated_mttr": "5-10 minutes"
  },
  "recommended_action": "Increase pool and restart services",
  "timeline": [
    {
      "type": "created",
      "timestamp": "2026-05-27T12:00:00Z",
      "message": "Incident detected"
    }
  ]
}
```

### Create Incident

**Endpoint:** `POST /api/incidents`

**Request Body:**
```json
{
  "type": "db_timeout|redis_unavailable|http_spike|high_latency",
  "severity": "low|medium|high|critical",
  "message": "Incident description",
  "logs": ["log entry 1", "log entry 2", ...]
}
```

**Response:**
```json
{
  "id": "generated-uuid",
  "type": "db_timeout",
  "severity": "high",
  "message": "Database connection timeout detected",
  "status": "open",
  "created_at": "2026-05-27T12:00:00Z",
  "timeline": [...]
}
```

**Status Codes:**
- 201: Incident created successfully
- 400: Invalid request
- 500: Server error

### Analyze Incident

**Endpoint:** `POST /api/incidents/:id/analyze`

**Description:** Triggers AI analysis of incident logs using Vertex AI Gemini.

**Request Body:** (empty)

**Response:**
```json
{
  "id": "incident-uuid",
  "analysis": {
    "root_cause": "Detailed root cause analysis",
    "confidence": 0.92,
    "affected_services": ["service1", "service2"],
    "estimated_impact": "High impact description",
    "estimated_mttr": "5-10 minutes",
    "logs_analyzed": 5
  },
  "analyzed_at": "2026-05-27T12:01:00Z"
}
```

**Status Codes:**
- 200: Analysis completed
- 404: Incident not found
- 500: Analysis failed

### Approve Remediation

**Endpoint:** `POST /api/incidents/:id/remediation/approve`

**Description:** Approves and executes remediation, generates postmortem.

**Request Body:** (empty)

**Response:**
```json
{
  "id": "incident-uuid",
  "status": "resolved",
  "remediation": {
    "status": "approved",
    "action": "Remediation description",
    "executed_at": "2026-05-27T12:02:00Z",
    "result": "Execution result"
  },
  "postmortem": "AI-generated postmortem report...",
  "resolved_at": "2026-05-27T12:02:00Z"
}
```

**Status Codes:**
- 200: Remediation approved and executed
- 404: Incident not found
- 500: Approval failed

### Get Incident Timeline

**Endpoint:** `GET /api/incidents/:id/timeline`

**Response:**
```json
[
  {
    "type": "created|analyzed|remediation_approved|resolved",
    "timestamp": "2026-05-27T12:00:00Z",
    "message": "Event description"
  },
  {
    "type": "analyzed",
    "timestamp": "2026-05-27T12:01:00Z",
    "message": "AI analysis completed"
  }
]
```

## AI Service (Python/FastAPI)

Base URL: `http://localhost:8000` (local) or `https://cloudops-ai-ai-service.run.app` (Cloud Run)

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "cloudops-ai-ai-service",
  "timestamp": "2026-05-27T12:00:00Z"
}
```

### Service Info

**Endpoint:** `GET /`

**Response:**
```json
{
  "service": "CloudOps AI - AI Agent Service",
  "version": "1.0.0",
  "endpoints": {
    "/health": "Health check",
    "/api/analyze": "Analyze logs",
    "/api/remediate": "Generate remediation",
    "/api/remediate-execute": "Execute remediation",
    "/api/postmortem": "Generate postmortem"
  }
}
```

### Analyze Logs

**Endpoint:** `POST /api/analyze`

**Request Body:**
```json
{
  "logs": ["log entry 1", "log entry 2", ...],
  "incident_type": "db_timeout|redis_unavailable|http_spike|high_latency"
}
```

**Response:**
```json
{
  "root_cause": "Technical explanation of root cause",
  "confidence": 0.92,
  "affected_services": ["service1", "service2"],
  "estimated_impact": "Critical - 100% request failure",
  "estimated_mttr": "5-10 minutes"
}
```

### Generate Remediation

**Endpoint:** `POST /api/remediate`

**Request Body:**
```json
{
  "incident_id": "incident-uuid",
  "root_cause": "Root cause from analysis",
  "service": "affected_service_name"
}
```

**Response:**
```json
{
  "action": "Primary remediation action",
  "severity": "high|medium|low",
  "steps": [
    "Step 1: description",
    "Step 2: description",
    "Step 3: description"
  ]
}
```

### Execute Remediation

**Endpoint:** `POST /api/remediate-execute`

**Request Body:**
```json
{
  "incident_id": "incident-uuid",
  "action": "Remediation action to execute"
}
```

**Response:**
```json
{
  "status": "executed",
  "message": "Remediation execution result",
  "execution_time": 2.5
}
```

### Generate Postmortem

**Endpoint:** `POST /api/postmortem`

**Request Body:**
```json
{
  "incident_id": "incident-uuid",
  "root_cause": "Root cause analysis",
  "remediation": "Remediation taken",
  "duration_minutes": 7
}
```

**Response:**
```json
{
  "postmortem": "Professional incident postmortem report\n\nIncludes:\n- Executive summary\n- Timeline\n- Root cause analysis\n- Remediation steps\n- Preventive measures"
}
```

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request - Invalid input
- **404**: Not Found - Resource doesn't exist
- **500**: Internal Server Error - Server-side error
- **503**: Service Unavailable - Service is down

## Rate Limiting

No built-in rate limiting in demo mode. For production:
- Recommended: 1000 requests/hour per IP
- AI Service calls limited to 100/hour due to Vertex AI quotas

## Authentication

Local development: No authentication required

Cloud Run deployment: Services are private by default, authenticated via Cloud Run service accounts and IAM.

## Pagination

List endpoints support pagination via query parameters:

```
GET /api/incidents?limit=20&offset=0
```

## Webhooks

Currently not implemented. For production:
- Incident creation webhooks
- Analysis completion webhooks
- Remediation status webhooks

## SDK Examples

### Node.js

```javascript
import axios from 'axios'

const client = axios.create({
  baseURL: 'http://localhost:3001'
})

// Create incident
const incident = await client.post('/api/incidents', {
  type: 'db_timeout',
  severity: 'high',
  message: 'Database timeout',
  logs: ['error 1', 'error 2']
})

// Analyze
const analysis = await client.post(
  `/api/incidents/${incident.data.id}/analyze`
)

// Approve remediation
const resolved = await client.post(
  `/api/incidents/${incident.data.id}/remediation/approve`
)
```

### Python

```python
import requests

client = requests.Session()
client.base_url = 'http://localhost:3001'

# Create incident
resp = client.post('/api/incidents', json={
    'type': 'db_timeout',
    'severity': 'high',
    'message': 'Database timeout',
    'logs': ['error 1', 'error 2']
})
incident_id = resp.json()['id']

# Analyze
client.post(f'/api/incidents/{incident_id}/analyze')

# Approve
client.post(f'/api/incidents/{incident_id}/remediation/approve')
```

### cURL

```bash
# Create incident
curl -X POST http://localhost:3001/api/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "type": "db_timeout",
    "severity": "high",
    "message": "Database timeout",
    "logs": ["error 1", "error 2"]
  }'

# List incidents
curl http://localhost:3001/api/incidents

# Analyze incident
curl -X POST http://localhost:3001/api/incidents/INCIDENT_ID/analyze

# Approve remediation
curl -X POST http://localhost:3001/api/incidents/INCIDENT_ID/remediation/approve
```

