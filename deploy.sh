#!/bin/bash

# CloudOps AI - Cloud Run Deployment Script
# Usage: ./deploy.sh <project-id> <region>

set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
REGION=${2:-us-central1}
REPO_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloudops-ai"

echo "🚀 CloudOps AI - Cloud Run Deployment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Repository: $REPO_URL"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
check_command() {
  if ! command -v $1 &> /dev/null; then
    echo -e "${RED}✗ $1 not found. Please install it first.${NC}"
    exit 1
  fi
}

log_step() {
  echo -e "${YELLOW}→ $1${NC}"
}

log_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
  echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
log_step "Checking prerequisites..."
check_command gcloud
check_command docker
log_success "All prerequisites installed"
echo ""

# Step 1: Enable APIs
log_step "Enabling GCP APIs..."
gcloud services enable \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com \
  logging.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  --project=$PROJECT_ID
log_success "APIs enabled"
echo ""

# Step 2: Create Artifact Registry
log_step "Creating Artifact Registry repository..."
if gcloud artifacts repositories describe cloudops-ai \
  --location=$REGION --project=$PROJECT_ID &>/dev/null; then
  log_success "Repository already exists"
else
  gcloud artifacts repositories create cloudops-ai \
    --repository-format=docker \
    --location=$REGION \
    --description="CloudOps AI Docker images" \
    --project=$PROJECT_ID
  log_success "Repository created"
fi
echo ""

# Step 3: Configure Docker
log_step "Configuring Docker authentication..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet
log_success "Docker configured"
echo ""

# Step 4: Build and push images
log_step "Building and pushing Docker images..."

# Frontend
echo "  → Frontend..."
docker build -t ${REPO_URL}/frontend:latest ./frontend
docker push ${REPO_URL}/frontend:latest
log_success "Frontend image pushed"

# Backend
echo "  → Backend..."
docker build -t ${REPO_URL}/backend:latest ./backend
docker push ${REPO_URL}/backend:latest
log_success "Backend image pushed"

# AI Service
echo "  → AI Service..."
docker build -t ${REPO_URL}/ai-service:latest ./ai-service
docker push ${REPO_URL}/ai-service:latest
log_success "AI Service image pushed"
echo ""

# Step 5: Deploy services
log_step "Deploying to Cloud Run..."

# AI Service (deploy first - backend depends on it)
echo "  → AI Service..."
gcloud run deploy cloudops-ai-ai-service \
  --image=${REPO_URL}/ai-service:latest \
  --platform=managed \
  --region=${REGION} \
  --memory=2Gi \
  --cpu=2 \
  --timeout=3600 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},VERTEX_AI_LOCATION=${REGION},VERTEX_AI_MODEL=gemini-1.5-flash-001,LLM_PROVIDER=vertex_ai" \
  --no-allow-unauthenticated \
  --project=$PROJECT_ID
log_success "AI Service deployed"

# Get AI Service URL
AI_SERVICE_URL=$(gcloud run services describe cloudops-ai-ai-service \
  --region=${REGION} \
  --format='value(status.url)' \
  --project=$PROJECT_ID)
echo "  AI Service URL: $AI_SERVICE_URL"
echo ""

# Backend
echo "  → Backend..."
gcloud run deploy cloudops-ai-backend \
  --image=${REPO_URL}/backend:latest \
  --platform=managed \
  --region=${REGION} \
  --memory=2Gi \
  --cpu=2 \
  --timeout=3600 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},FIRESTORE_COLLECTION=incidents,PUBSUB_TOPIC=incident-events,AI_SERVICE_URL=${AI_SERVICE_URL}" \
  --no-allow-unauthenticated \
  --project=$PROJECT_ID
log_success "Backend deployed"

# Get Backend URL
BACKEND_URL=$(gcloud run services describe cloudops-ai-backend \
  --region=${REGION} \
  --format='value(status.url)' \
  --project=$PROJECT_ID)
echo "  Backend URL: $BACKEND_URL"
echo ""

# Frontend
echo "  → Frontend..."
gcloud run deploy cloudops-ai-frontend \
  --image=${REPO_URL}/frontend:latest \
  --platform=managed \
  --region=${REGION} \
  --memory=1Gi \
  --cpu=1 \
  --set-env-vars="REACT_APP_API_URL=${BACKEND_URL}" \
  --allow-unauthenticated \
  --project=$PROJECT_ID
log_success "Frontend deployed"

# Get Frontend URL
FRONTEND_URL=$(gcloud run services describe cloudops-ai-frontend \
  --region=${REGION} \
  --format='value(status.url)' \
  --project=$PROJECT_ID)
echo "  Frontend URL: $FRONTEND_URL"
echo ""

# Step 6: Display summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Access your application:"
echo -e "  ${GREEN}Frontend:${NC}    ${FRONTEND_URL}"
echo -e "  ${GREEN}Backend:${NC}     ${BACKEND_URL}"
echo -e "  ${GREEN}AI Service:${NC}  ${AI_SERVICE_URL}"
echo ""
echo "Next steps:"
echo "  1. Create Firestore database (if not exists)"
echo "  2. Create service account with Vertex AI permissions"
echo "  3. Monitor services: gcloud logging read --limit=50"
echo "  4. View Cloud Run dashboard: https://console.cloud.google.com/run"
echo ""
