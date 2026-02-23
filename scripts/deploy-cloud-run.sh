#!/bin/bash

# Deploy Knowledge Graph Platform to Google Cloud Run
PROJECT_ID="knowledge-graph-platform"
REGION="us-central1"

echo "=== Deploying to Google Cloud Run ==="

# Build and deploy main API
echo "Building and deploying main API..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/kg-api:latest \
    --config cloudbuild.yaml .

# Deploy main API with secrets
gcloud run deploy kg-api \
    --image gcr.io/$PROJECT_ID/kg-api:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --concurrency 1000 \
    --max-instances 10 \
    --set-secrets POSTGRES_PASSWORD=postgres-password:latest \
    --set-secrets NEO4J_PASSWORD=neo4j-password:latest \
    --set-secrets NEO4J_URI=neo4j-uri:latest \
    --set-secrets OPENAI_API_KEY=openai-api-key:latest \
    --set-env-vars POSTGRES_HOST=172.17.0.1 \
    --set-env-vars POSTGRES_DB=logistics_kg \
    --set-env-vars POSTGRES_USER=postgres \
    --set-env-vars NEO4J_USER=neo4j \
    --set-env-vars LOG_LEVEL=INFO

# Deploy compliance engine
echo "Building and deploying compliance engine..."
gcloud run deploy kg-compliance \
    --image gcr.io/$PROJECT_ID/kg-compliance:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --concurrency 1000 \
    --max-instances 10 \
    --set-secrets POSTGRES_PASSWORD=postgres-password:latest \
    --set-secrets NEO4J_PASSWORD=neo4j-password:latest \
    --set-secrets NEO4J_URI=neo4j-uri:latest \
    --set-env-vars POSTGRES_HOST=172.17.0.1 \
    --set-env-vars POSTGRES_DB=logistics_kg \
    --set-env-vars POSTGRES_USER=postgres \
    --set-env-vars NEO4J_USER=neo4j \
    --set-env-vars LOG_LEVEL=INFO

# Get service URLs
API_URL=$(gcloud run services describe kg-api --region $REGION --format="value(status.url)")
COMPLIANCE_URL=$(gcloud run services describe kg-compliance --region $REGION --format="value(status.url)")

echo "=== Deployment Complete ==="
echo "Main API URL: $API_URL"
echo "Compliance API URL: $COMPLIANCE_URL"
echo ""
echo "=== Test the deployment ==="
echo "curl $API_URL/health"
echo "curl $COMPLIANCE_URL/health"
