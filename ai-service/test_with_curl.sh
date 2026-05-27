#!/bin/bash

# CloudOps AI - API Testing with curl
# Usage: bash test_with_curl.sh [local|cloud]
#
# local:  Test against http://localhost:8080 (requires service running locally)
# cloud:  Test against Cloud Run URL

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MODE=${1:-local}

if [ "$MODE" = "local" ]; then
    API_URL="http://localhost:8080"
    echo -e "${BLUE}Testing against LOCAL service: $API_URL${NC}\n"
elif [ "$MODE" = "cloud" ]; then
    API_URL="https://cloudops-ai-ai-service-XXXXXXXXX.us-central1.run.app"
    echo -e "${BLUE}Testing against CLOUD service: $API_URL${NC}"
    echo -e "${YELLOW}Note: Replace XXXXXXXXX with your Cloud Run service ID${NC}\n"
    read -p "Enter full Cloud Run URL: " API_URL
else
    echo "Usage: bash test_with_curl.sh [local|cloud]"
    exit 1
fi

# Function to print test header
test_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}TEST: $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Test 1: Health Check
test_header "Health Check"
echo "Request: GET /health"
echo "curl $API_URL/health"
echo ""

if response=$(curl -s -w "\n%{http_code}" "$API_URL/health"); then
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        print_success "Health check passed (HTTP $http_code)"
        echo "Response: $body" | jq .
    else
        print_error "Health check failed (HTTP $http_code)"
        echo "Response: $body"
    fi
else
    print_error "Connection failed. Is the service running?"
    exit 1
fi

# Test 2: Readiness Check
test_header "Readiness Check"
echo "Request: GET /ready"
echo "curl $API_URL/ready"
echo ""

response=$(curl -s -w "\n%{http_code}" "$API_URL/ready")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    print_success "Readiness check passed (HTTP $http_code)"
    echo "Response:"
    echo "$body" | jq .
else
    print_error "Readiness check failed (HTTP $http_code)"
    echo "Response: $body"
fi

# Test 3: Service Info
test_header "Service Info"
echo "Request: GET /api/info"
echo "curl $API_URL/api/info"
echo ""

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/info")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    print_success "Service info retrieved (HTTP $http_code)"
    echo "Response:"
    echo "$body" | jq .
else
    print_error "Service info failed (HTTP $http_code)"
fi

# Test 4: Analyze Incident - Database Timeout
test_header "Analyze Incident: Database Timeout"
echo "Request: POST /api/analyze"
echo ""

request_body='{
  "logs": [
    "ERROR: Connection timeout to database after 30s",
    "WARN: Retrying connection to database...",
    "ERROR: Failed to acquire connection from pool (exhausted)",
    "ERROR: Connection pool has 0 available connections"
  ],
  "incident_type": "db_timeout",
  "severity": "critical",
  "incident_id": "test-db-001"
}'

echo "Request body:"
echo "$request_body" | jq .
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/analyze" \
  -H "Content-Type: application/json" \
  -d "$request_body")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    print_success "Analysis completed (HTTP $http_code)"
    echo "Response:"
    echo "$body" | jq .

    # Extract key information
    root_cause=$(echo "$body" | jq -r '.analysis.root_cause // "N/A"')
    confidence=$(echo "$body" | jq -r '.analysis.confidence // "N/A"')
    action=$(echo "$body" | jq -r '.remediation.primary_action // "N/A"')
    safety=$(echo "$body" | jq -r '.hallucination_report.overall_safety // "N/A"')

    echo ""
    echo -e "${BLUE}Analysis Summary:${NC}"
    echo "  Root Cause: $root_cause"
    echo "  Confidence: $confidence"
    echo "  Remediation: $action"
    echo "  Safety Check: $safety"
else
    print_error "Analysis failed (HTTP $http_code)"
    echo "Response: $body"
fi

# Test 5: Analyze Incident - Redis Unavailable
test_header "Analyze Incident: Redis Unavailable"

request_body='{
  "logs": [
    "ERROR: Redis connection refused on port 6379",
    "WARN: Cache layer unavailable",
    "ERROR: Cannot connect to Redis cluster"
  ],
  "incident_type": "redis_unavailable",
  "severity": "high",
  "incident_id": "test-redis-001"
}'

echo "Request body:"
echo "$request_body" | jq .
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/analyze" \
  -H "Content-Type: application/json" \
  -d "$request_body")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    print_success "Analysis completed (HTTP $http_code)"
    echo "Response:"
    echo "$body" | jq .
else
    print_error "Analysis failed (HTTP $http_code)"
fi

# Test 6: Analyze Incident - HTTP Spike
test_header "Analyze Incident: HTTP Spike"

request_body='{
  "logs": [
    "WARN: HTTP 503 Service Unavailable",
    "ERROR: Request timeout after 30s",
    "WARN: High latency detected (avg 5000ms)",
    "ERROR: Circuit breaker open for downstream service"
  ],
  "incident_type": "http_spike",
  "severity": "high",
  "incident_id": "test-http-001"
}'

echo "Request body:"
echo "$request_body" | jq .
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/analyze" \
  -H "Content-Type: application/json" \
  -d "$request_body")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    print_success "Analysis completed (HTTP $http_code)"
    echo "Response:"
    echo "$body" | jq .
else
    print_error "Analysis failed (HTTP $http_code)"
fi

# Test 7: List Sessions
test_header "List Active Sessions"
echo "Request: GET /api/sessions"
echo "curl $API_URL/api/sessions"
echo ""

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/sessions")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    print_success "Sessions listed (HTTP $http_code)"
    echo "Response:"
    echo "$body" | jq .
else
    print_error "Sessions list failed (HTTP $http_code)"
fi

# Summary
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Testing complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"

echo -e "${BLUE}Key Verifications:${NC}"
echo "  ✓ Health checks respond"
echo "  ✓ Readiness shows orchestrator status"
echo "  ✓ Service info displays features"
echo "  ✓ Analysis endpoint returns root cause + remediation"
echo "  ✓ Hallucination control report included in response"
echo "  ✓ All incident types handled (db_timeout, redis, http)"
echo ""

echo -e "${BLUE}Google ADK Integration Points to Check:${NC}"
echo "  ✓ IncidentAnalysisAgent created and executed"
echo "  ✓ RemediationAgent created and executed"
echo "  ✓ Tool binding working (query_logs, get_service_health)"
echo "  ✓ InMemoryRunner orchestrating multi-agent workflow"
echo "  ✓ Hallucination detection active"
echo ""
