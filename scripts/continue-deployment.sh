#!/bin/bash

# Continue Google Cloud Deployment
set -e

# Configuration
PROJECT_ID="knowledge-graph-1771880019"
REGION="us-central1"
NEO4J_URI="neo4j+s://da9befad.databases.neo4j.io"
NEO4J_PASSWORD="WSwqgYFZWpATj0n1lLBwq6PX__u0veDSZpFZiz99g3U"

export PATH="/Users/mehrdadmohamadali/Desktop/Knowledge Graph/google-cloud-sdk/google-cloud-sdk/bin:$PATH"

echo "🚀 Continuing Google Cloud Deployment"
echo "=================================="

# Set project
gcloud config set project $PROJECT_ID

# Get database password
DB_PASSWORD=$(openssl rand -base64 32)
DB_CONNECTION_NAME="knowledge-graph-1771880019:us-central1:knowledge-graph-db"

echo "🔐 Setting up Secret Manager..."

# Update Neo4j secrets
echo "  🔐 Updating Neo4j secrets..."
echo -n $NEO4J_URI | gcloud secrets versions add neo4j-uri --data-file=-
echo -n $NEO4J_PASSWORD | gcloud secrets versions add neo4j-password --data-file=-

# Update database secrets
echo "  🔐 Updating database secrets..."
echo -n $DB_PASSWORD | gcloud secrets versions add postgres-password --data-file=-
echo -n $DB_CONNECTION_NAME | gcloud secrets versions add postgres-connection --data-file=-

# Grant secret access
echo "  🔐 Granting secret access..."
gcloud secrets add-iam-policy-binding neo4j-uri \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding neo4j-password \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding postgres-password \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding postgres-connection \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

echo "✅ Secret Manager setup complete"

# Build and deploy services
echo "🐳 Building and deploying services..."

# Build main API
echo "  🚀 Building main API..."
docker build --platform linux/amd64 -f backend/Dockerfile.cloud -t gcr.io/$PROJECT_ID/kg-api:latest .
docker push gcr.io/$PROJECT_ID/kg-api:latest

# Build compliance engine
echo "  🛡️ Building compliance engine..."
docker build --platform linux/amd64 -f backend/Dockerfile.compliance.cloud -t gcr.io/$PROJECT_ID/kg-compliance:latest .
docker push gcr.io/$PROJECT_ID/kg-compliance:latest

# Build AI Studio API
echo "  🤖 Building AI Studio API..."
docker build --platform linux/amd64 -f backend/Dockerfile.ai-studio -t gcr.io/$PROJECT_ID/kg-ai-studio:latest .
docker push gcr.io/$PROJECT_ID/kg-ai-studio:latest

# Deploy services
echo "🚀 Deploying services..."

# Deploy main API
echo "  🚀 Deploying main API..."
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
    --set-secrets POSTGRES_CONNECTION=postgres-connection:latest \
    --set-env-vars POSTGRES_DB=logistics_kg \
    --set-env-vars POSTGRES_USER=postgres \
    --set-env-vars NEO4J_USER=neo4j \
    --set-env-vars LOG_LEVEL=INFO

# Deploy compliance engine
echo "  🛡️ Deploying compliance engine..."
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
    --set-secrets POSTGRES_CONNECTION=postgres-connection:latest \
    --set-env-vars POSTGRES_DB=logistics_kg \
    --set-env-vars POSTGRES_USER=postgres \
    --set-env-vars NEO4J_USER=neo4j \
    --set-env-vars LOG_LEVEL=INFO

# Deploy AI Studio API
echo "  🤖 Deploying AI Studio API..."
gcloud run deploy kg-ai-studio \
    --image gcr.io/$PROJECT_ID/kg-ai-studio:latest \
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
    --set-secrets POSTGRES_CONNECTION=postgres-connection:latest \
    --set-env-vars POSTGRES_DB=logistics_kg \
    --set-env-vars POSTGRES_USER=postgres \
    --set-env-vars NEO4J_USER=neo4j \
    --set-env-vars LOG_LEVEL=INFO

# Get service URLs
API_URL=$(gcloud run services describe kg-api --region $REGION --format="value(status.url)")
COMPLIANCE_URL=$(gcloud run services describe kg-compliance --region $REGION --format="value(status.url)")
AI_STUDIO_URL=$(gcloud run services describe kg-ai-studio --region $REGION --format="value(status.url)")

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo ""
echo "🌐 Service URLs:"
echo "  Main API: $API_URL"
echo "  Compliance Engine: $COMPLIANCE_URL"
echo "  AI Studio API: $AI_STUDIO_URL"
echo ""
echo "📚 API Documentation:"
echo "  Main API: $API_URL/docs"
echo "  Compliance API: $COMPLIANCE_URL/docs"
echo "  AI Studio API: $AI_STUDIO_URL/docs"
echo ""
echo "🔧 Environment Variables for AI Studio:"
echo "  KG_API_URL=$API_URL"
echo "  VITE_KG_API_URL=$AI_STUDIO_URL"
echo ""
echo "✅ Your Knowledge Graph Platform is now live on Google Cloud!"
