# CloudOps AI - GCP Setup & Deployment Guide

Complete step-by-step guide to set up and deploy CloudOps AI on Google Cloud Platform.

## Prerequisites

- GCP Project (new or existing)
- gcloud CLI installed and configured
- `gcloud auth login` completed
- `gcloud config set project YOUR_PROJECT_ID`

## Step 1: Enable Required GCP APIs

```bash
PROJECT_ID=$(gcloud config get-value project)

# Enable required APIs
gcloud services enable \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com \
  logging.googleapis.com \
  run.googleapis.com \
  compute.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

echo "✓ All APIs enabled for project: $PROJECT_ID"
```

## Step 2: Set Up Firestore

```bash
# Create Firestore database (choose location - us-central1 recommended)
gcloud firestore databases create \
  --location=us-central1 \
  --type=firestore-native

echo "✓ Firestore database created"
```

Initialize collections by running this once after backend is up:

```bash
cat > init_firestore.js << 'INIT'
const admin = require('firebase-admin');
const serviceAccount = require('./service-account-key.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  projectId: process.env.GOOGLE_CLOUD_PROJECT
});

const db = admin.firestore();

async function initCollections() {
  console.log('Initializing Firestore collections...');
  
  // Create incidents collection
  await db.collection('incidents').doc('_init').set({
    initialized: true,
    timestamp: new Date()
  });
  
  console.log('✓ Collections initialized');
  process.exit(0);
}

initCollections().catch(console.error);
INIT

node init_firestore.js
```

## Step 3: Set Up Pub/Sub Topics

```bash
# Create incident events topic
gcloud pubsub topics create incident-events

# Create subscriptions
gcloud pubsub subscriptions create incident-events-sub \
  --topic=incident-events

echo "✓ Pub/Sub topics and subscriptions created"
```

## Step 4: Create Service Account for Application

```bash
# Create service account
gcloud iam service-accounts create cloudops-ai-app \
  --display-name="CloudOps AI Application"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloudops-ai-app@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloudops-ai-app@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloudops-ai-app@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/pubsub.editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloudops-ai-app@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

echo "✓ Service account created with necessary roles"
```

## Step 5: Create Service Account Key (Local Development)

```bash
PROJECT_ID=$(gcloud config get-value project)

gcloud iam service-accounts keys create key.json \
  --iam-account=cloudops-ai-app@$PROJECT_ID.iam.gserviceaccount.com

# Set for local development
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key.json"

echo "✓ Service account key created"
```

## Step 6: Set Environment Variables

Create `.env` files for each service:

### Backend (.env)
```bash
GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
FIRESTORE_COLLECTION=incidents
AI_SERVICE_URL=http://localhost:8000
PUBSUB_TOPIC=incident-events
PORT=3001
NODE_ENV=development
```

### AI Service (.env)
```bash
GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-1.5-flash-001
LLM_PROVIDER=vertex_ai
PORT=8000
```

## Step 7: Create Artifact Registry (for Docker images)

```bash
REGION=us-central1

# Create repository
gcloud artifacts repositories create cloudops-ai \
  --repository-format=docker \
  --location=$REGION \
  --description="CloudOps AI Docker images"

# Configure Docker authentication
gcloud auth configure-docker ${REGION}-docker.pkg.dev

echo "✓ Artifact Registry created"
```

## Step 8: Build and Push Docker Images

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
REPO_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloudops-ai"

# Build and push frontend
echo "Building frontend..."
docker build -t ${REPO_URL}/frontend:latest ./frontend
docker push ${REPO_URL}/frontend:latest

# Build and push backend
echo "Building backend..."
docker build -t ${REPO_URL}/backend:latest ./backend
docker push ${REPO_URL}/backend:latest

# Build and push AI service
echo "Building AI service..."
docker build -t ${REPO_URL}/ai-service:latest ./ai-service
docker push ${REPO_URL}/ai-service:latest

echo "✓ All images pushed to Artifact Registry"
```

## Step 9: Deploy to Cloud Run

### Deploy AI Service First (Backend depends on it)

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
REPO_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloudops-ai"

# Deploy AI Service
echo "Deploying AI service..."
gcloud run deploy cloudops-ai-ai-service \
  --image=${REPO_URL}/ai-service:latest \
  --platform=managed \
  --region=${REGION} \
  --memory=2Gi \
  --cpu=2 \
  --timeout=3600 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},VERTEX_AI_LOCATION=${REGION},VERTEX_AI_MODEL=gemini-1.5-flash-001,LLM_PROVIDER=vertex_ai" \
  --no-allow-unauthenticated \
  --service-account=cloudops-ai-app@${PROJECT_ID}.iam.gserviceaccount.com

# Get AI service URL
AI_SERVICE_URL=$(gcloud run services describe cloudops-ai-ai-service --region=${REGION} --format='value(status.url)')
echo "AI Service URL: $AI_SERVICE_URL"
```

### Deploy Backend

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
REPO_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloudops-ai"

# Deploy Backend
echo "Deploying backend..."
gcloud run deploy cloudops-ai-backend \
  --image=${REPO_URL}/backend:latest \
  --platform=managed \
  --region=${REGION} \
  --memory=2Gi \
  --cpu=2 \
  --timeout=3600 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},FIRESTORE_COLLECTION=incidents,PUBSUB_TOPIC=incident-events,AI_SERVICE_URL=${AI_SERVICE_URL}" \
  --no-allow-unauthenticated \
  --service-account=cloudops-ai-app@${PROJECT_ID}.iam.gserviceaccount.com

# Get Backend URL
BACKEND_URL=$(gcloud run services describe cloudops-ai-backend --region=${REGION} --format='value(status.url)')
echo "Backend URL: $BACKEND_URL"
```

### Deploy Frontend

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
REPO_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloudops-ai"

# Deploy Frontend
echo "Deploying frontend..."
gcloud run deploy cloudops-ai-frontend \
  --image=${REPO_URL}/frontend:latest \
  --platform=managed \
  --region=${REGION} \
  --memory=1Gi \
  --cpu=1 \
  --set-env-vars="REACT_APP_API_URL=${BACKEND_URL}" \
  --allow-unauthenticated

# Get Frontend URL
FRONTEND_URL=$(gcloud run services describe cloudops-ai-frontend --region=${REGION} --format='value(status.url)')
echo "Frontend URL: $FRONTEND_URL"
```

## Step 10: Configure Service-to-Service Authentication

Allow backend and frontend to call other services:

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1

# Allow backend to call AI service
gcloud run services add-iam-policy-binding cloudops-ai-ai-service \
  --region=${REGION} \
  --member="serviceAccount:cloudops-ai-backend@run.gserviceaccount.com" \
  --role="roles/run.invoker"

# If using Cloud Identity, allow frontend service account
gcloud run services add-iam-policy-binding cloudops-ai-backend \
  --region=${REGION} \
  --member="serviceAccount:cloudops-ai-frontend@run.gserviceaccount.com" \
  --role="roles/run.invoker"
```

## Step 11: Configure Firestore Security Rules

```bash
cat > firestore-rules.txt << 'RULES'
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow service account to read/write
    match /{document=**} {
      allow read, write: if request.auth.uid != null;
      allow read, write: if request.auth == null && request.headers['authorization'] != null;
    }
  }
}
RULES

gcloud firestore security-rules update firestore-rules.txt
```

For development (not recommended for production):
```bash
gcloud firestore security-rules update --source firestore-rules.txt
```

## Step 12: Verify Deployment

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1

echo "Checking service status..."

gcloud run services describe cloudops-ai-frontend --region=${REGION}
gcloud run services describe cloudops-ai-backend --region=${REGION}
gcloud run services describe cloudops-ai-ai-service --region=${REGION}

echo "✓ All services deployed successfully"
```

## Step 13: Monitor Logs

```bash
# View frontend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cloudops-ai-frontend" --limit 50

# View backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cloudops-ai-backend" --limit 50

# View AI service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cloudops-ai-ai-service" --limit 50
```

## Step 14: Create Cloud Run Traffic Management (Optional)

Split traffic between versions:
```bash
gcloud run services update-traffic cloudops-ai-frontend \
  --to-revisions LATEST=100
```

## Cleanup

To delete all resources:

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1

# Delete Cloud Run services
gcloud run services delete cloudops-ai-frontend --region=${REGION} --quiet
gcloud run services delete cloudops-ai-backend --region=${REGION} --quiet
gcloud run services delete cloudops-ai-ai-service --region=${REGION} --quiet

# Delete Firestore database
gcloud firestore databases delete --quiet

# Delete Pub/Sub resources
gcloud pubsub subscriptions delete incident-events-sub --quiet
gcloud pubsub topics delete incident-events --quiet

# Delete Artifact Registry images
gcloud artifacts repositories delete cloudops-ai --location=${REGION} --quiet

# Delete service account
gcloud iam service-accounts delete cloudops-ai-app@${PROJECT_ID}.iam.gserviceaccount.com --quiet

echo "✓ All resources cleaned up"
```

## Troubleshooting

### "Permission denied" errors
- Verify service account has correct roles
- Check `gcloud auth application-default login`

### Firestore connection issues
- Ensure Firestore database is created
- Check firestore-rules.txt is applied
- Verify service account has datastore.user role

### Vertex AI API errors
- Ensure aiplatform.googleapis.com is enabled
- Check region matches VERTEX_AI_LOCATION
- Verify model name is correct (gemini-1.5-flash-001)

### Cloud Run deployment fails
- Check Docker image exists in Artifact Registry
- Verify image name and region are correct
- Check service account has necessary roles

### Cross-service communication failures
- Verify Cloud Run services are in same region
- Check IAM bindings for service-to-service auth
- Review Cloud Run logs for specific errors

## Cost Estimation

**Monthly estimate for light usage:**
- Vertex AI API: ~$5-20 (depends on request volume)
- Cloud Run: ~$5-15 (compute time)
- Firestore: ~$5 (free tier + minimal reads/writes)
- Cloud Logging: Free (within limits)
- Artifact Registry: ~$0.10 (storage)

**Total: ~$15-50/month**

## Next Steps

1. Access frontend URL from Step 12
2. Click "Simulate Outage" to test workflow
3. Monitor logs in Cloud Logging
4. Set up Cloud Monitoring dashboards
5. Connect to real production logs (optional)

## Support

Refer to component READMEs for service-specific issues.
