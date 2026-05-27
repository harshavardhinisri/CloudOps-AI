# CloudOps AI - GCP Cloud Console UI Setup Guide

Complete step-by-step guide using Google Cloud Console (web UI) - no command line needed!

## Prerequisites

1. Google Account
2. GCP Free Tier Project (or create new one)
3. Docker Desktop (for building images)
4. Web browser

## Step 1: Create GCP Project (UI)

1. Go to https://console.cloud.google.com/
2. Click **"Select a Project"** (top left)
3. Click **"NEW PROJECT"**
4. Name: `cloudops-ai-demo`
5. Click **"CREATE"**
6. Wait for it to create (1-2 minutes)
7. Select your new project

**Save your Project ID** - you'll need it!

## Step 2: Enable APIs (UI)

1. In Cloud Console, search for **"APIs & Services"** (top search bar)
2. Click **"APIs & Services"** → **"Library"**
3. Search and enable each of these (click each, then "ENABLE"):

   - **Vertex AI API**
   - **Cloud Firestore API**
   - **Cloud Pub/Sub API**
   - **Cloud Logging API**
   - **Cloud Run API**
   - **Artifact Registry API**
   - **Cloud Build API**

**Takes 5-10 minutes for all to enable**

## Step 3: Create Firestore Database (UI)

1. Search **"Firestore"** in Cloud Console
2. Click **"Firestore"** → **"Create Database"**
3. Select region: **us-central1**
4. Select mode: **Native mode**
5. Click **"CREATE DATABASE"**
6. Wait for creation (2-3 minutes)

## Step 4: Create Pub/Sub Topic (UI)

1. Search **"Pub/Sub"** in Cloud Console
2. Click **"Pub/Sub"** → **"Topics"**
3. Click **"CREATE TOPIC"**
4. Name: `incident-events`
5. Click **"CREATE"**
6. Click the topic you created
7. Click **"CREATE SUBSCRIPTION"**
8. Name: `incident-events-sub`
9. Click **"CREATE"**

## Step 5: Create Service Account (UI)

1. Search **"Service Accounts"** in Cloud Console
2. Click **"Service Accounts"**
3. Click **"CREATE SERVICE ACCOUNT"**
4. Name: `cloudops-ai-app`
5. Description: `CloudOps AI Application`
6. Click **"CREATE AND CONTINUE"**
7. Click **"CONTINUE"** (skip optional steps)
8. Click **"DONE"**

## Step 6: Grant Permissions (UI)

1. In Service Accounts, click **`cloudops-ai-app`**
2. Go to **"PERMISSIONS"** tab (top)
3. Click **"GRANT ACCESS"**
4. In "New principals", paste service account email
5. Add these **Roles** (click "ADD ANOTHER ROLE" each time):
   - `Vertex AI User`
   - `Cloud Datastore User`
   - `Pub/Sub Editor`
   - `Cloud Logging Writer`
6. Click **"SAVE"**

## Step 7: Create Artifact Registry (UI)

1. Search **"Artifact Registry"** in Cloud Console
2. Click **"Artifact Registry"** → **"Repositories"**
3. Click **"CREATE REPOSITORY"**
4. Name: `cloudops-ai`
5. Format: `Docker`
6. Location: `us-central1`
7. Click **"CREATE"**

## Step 8: Build & Push Docker Images

You need Docker Desktop for this part. Run these commands:

```bash
cd ~/CloudOps-AI

# Get your project ID
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1

# Configure Docker
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build and push frontend
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloudops-ai/frontend:latest ./frontend
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloudops-ai/frontend:latest

# Build and push backend
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloudops-ai/backend:latest ./backend
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloudops-ai/backend:latest

# Build and push AI service
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloudops-ai/ai-service:latest ./ai-service
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloudops-ai/ai-service:latest
```

## Step 9: Deploy AI Service (UI)

1. Search **"Cloud Run"** in Cloud Console
2. Click **"Cloud Run"** → **"DEPLOY"** (or "CREATE SERVICE")
3. Configure:
   - **Service name:** `cloudops-ai-ai-service`
   - **Region:** `us-central1`
   - **Container image URL:** (paste from Artifact Registry → ai-service → copy full URL)
   - **Deployment settings:**
     - Memory: `2 GB`
     - CPU: `2`
     - Timeout: `3600 seconds`
     - Execution environment: `2nd gen`
4. Click **"DEPLOY"**
5. Wait for deployment (5 minutes)
6. **Copy the service URL** - you'll need it for backend!

## Step 10: Deploy Backend (UI)

1. Click **"Cloud Run"** → **"CREATE SERVICE"**
2. Configure:
   - **Service name:** `cloudops-ai-backend`
   - **Region:** `us-central1`
   - **Container image URL:** (paste backend URL from Artifact Registry)
   - **Deployment settings:**
     - Memory: `2 GB`
     - CPU: `2`
     - Timeout: `3600 seconds`
3. Click **"RUNTIME SETTINGS"** (expand)
4. **Environment variables** - click "ADD VARIABLE" for each:
   ```
   GOOGLE_CLOUD_PROJECT = your-project-id
   FIRESTORE_COLLECTION = incidents
   AI_SERVICE_URL = https://cloudops-ai-ai-service-xxxxx.run.app
   PUBSUB_TOPIC = incident-events
   ```
5. Click **"DEPLOY"**
6. Wait for deployment (5 minutes)
7. **Copy the service URL** - you'll need it for frontend!

## Step 11: Deploy Frontend (UI)

1. Click **"Cloud Run"** → **"CREATE SERVICE"**
2. Configure:
   - **Service name:** `cloudops-ai-frontend`
   - **Region:** `us-central1`
   - **Container image URL:** (paste frontend URL from Artifact Registry)
   - **Deployment settings:**
     - Memory: `1 GB`
     - CPU: `1`
     - Timeout: `3600 seconds`
3. Click **"RUNTIME SETTINGS"** (expand)
4. **Environment variables** - click "ADD VARIABLE":
   ```
   REACT_APP_API_URL = https://cloudops-ai-backend-xxxxx.run.app
   ```
5. **Allow unauthenticated invocations** - Toggle ON
6. Click **"DEPLOY"**
7. Wait for deployment (5 minutes)

## Step 12: Access Your App

Once all 3 services are deployed:

1. Go to **"Cloud Run"** in Cloud Console
2. Click **`cloudops-ai-frontend`**
3. Click the **Service URL** (shown at top)
4. 🎉 Your app is live!

---

## Your URLs

After deployment, you have 3 public URLs:

```
Frontend:   https://cloudops-ai-frontend-xxxxx.run.app
Backend:    https://cloudops-ai-backend-xxxxx.run.app
AI Service: https://cloudops-ai-ai-service-xxxxx.run.app
```

**Only share the Frontend URL for demo!**

---

## Testing

1. Open Frontend URL
2. Click **"Simulate Outage"**
3. Click **"Analyze"**
4. Watch it use **real Vertex AI Gemini Flash**
5. Click **"Approve & Execute"**
6. View postmortem

---

## Delete Everything After Demo (UI)

### Delete Cloud Run Services

1. Go to **"Cloud Run"**
2. Select each service (cloudops-ai-frontend, cloudops-ai-backend, cloudops-ai-ai-service)
3. Click **"DELETE"**
4. Confirm

### Delete Firestore

1. Search **"Firestore"**
2. Click **"Databases"**
3. Click the database you created
4. Click **"DELETE DATABASE"**

### Delete Artifact Registry

1. Search **"Artifact Registry"**
2. Click **"Repositories"**
3. Click `cloudops-ai`
4. Click **"DELETE"**

### Delete Pub/Sub

1. Search **"Pub/Sub"**
2. Click **"Topics"** → Delete `incident-events`
3. Click **"Subscriptions"** → Delete `incident-events-sub`

---

## Cost Tracking (UI)

1. Search **"Billing"** in Cloud Console
2. Click **"Billing"** → **"Budgets and alerts"**
3. Set a budget alert for safety

---

## Troubleshooting

### Service won't start?
- Check **Cloud Run logs** → Click service → "LOGS" tab
- Look for error messages

### Images not found?
- Check **Artifact Registry** → Make sure images are there
- Verify correct image URLs in Cloud Run deployment

### Firestore permission errors?
- Re-check Service Account permissions (Step 6)
- Make sure "Cloud Datastore User" role is assigned

### AI Service failing?
- Check Vertex AI API is enabled (Step 2)
- Check logs in Cloud Run service

---

## Quick Reference

| What | Where in Console |
|------|-----------------|
| Enable APIs | APIs & Services → Library |
| Create Firestore | Search "Firestore" |
| Create Pub/Sub | Search "Pub/Sub" |
| Service Account | Search "Service Accounts" |
| Artifact Registry | Search "Artifact Registry" |
| Deploy & view | Search "Cloud Run" |
| Logs | Cloud Run service → Logs tab |
| Monitoring | Cloud Run service → Metrics tab |

---

## Timeline

- **Total setup time:** ~45-60 minutes
- **API enablement:** 5-10 min
- **Image building:** 10-15 min
- **Cloud Run deployments:** 3 × 5 min = 15 min
- **Testing:** 5 min

---

That's it! All done through the UI! 🎉
