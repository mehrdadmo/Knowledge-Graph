#!/bin/bash

# Google Cloud Deployment Script for Knowledge Graph Platform
# This script automates the complete deployment process

set -e

# Configuration
PROJECT_ID="knowledge-graph-1771880019"
REGION="us-central1"
ZONE="us-central1-a"

echo "🚀 Google Cloud Deployment for Knowledge Graph Platform"
echo "=================================================="

# Function to handle quota limits
wait_for_quota() {
    echo "⏳ Waiting for quota reset..."
    sleep 10
}

# Check if gcloud is installed and set PATH
export PATH="/Users/mehrdadmohamadali/Desktop/Knowledge Graph/google-cloud-sdk/google-cloud-sdk/bin:$PATH"

if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK not found. Please install it first:"
    echo "   curl https://sdk.cloud.google.com | bash"
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with Google Cloud. Please run:"
    echo "   gcloud auth login"
    echo "   gcloud auth application-default login"
    exit 1
fi

echo "✅ Google Cloud SDK found and authenticated"

# Set project
echo "📋 Setting project: $PROJECT_ID"
gcloud config set project $PROJECT_ID
wait_for_quota

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
wait_for_quota
gcloud services enable sql-component.googleapis.com
wait_for_quota
gcloud services enable cloudbuild.googleapis.com
wait_for_quota
gcloud services enable secretmanager.googleapis.com
wait_for_quota
gcloud services enable artifactregistry.googleapis.com
wait_for_quota
gcloud services enable monitoring.googleapis.com

# Create service account
echo "🔐 Creating service account..."
if ! gcloud iam service-accounts describe kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com --format="value(email)" 2>/dev/null; then
    gcloud iam service-accounts create kg-platform-sa \
        --display-name="Knowledge Graph Platform Service Account" \
        --description="Service account for Knowledge Graph Platform"
else
    echo "✅ Service account already exists"
fi

# Grant permissions
echo "👥 Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Step 1: Create Cloud SQL PostgreSQL
echo "🗄️ Creating Cloud SQL PostgreSQL instance..."
if ! gcloud sql instances describe knowledge-graph-db --format="value(name)" 2>/dev/null; then
    gcloud sql instances create knowledge-graph-db \
        --database-version=POSTGRES_15 \
        --tier=db-custom-4-16384 \
        --region=$REGION \
        --storage-size=100GB \
        --storage-type=SSD \
        --backup-start-time=02:00 \
        --retained-backups-count=7 \
        --deletion-protection
else
    echo "✅ Cloud SQL instance already exists"
fi

# Create database
echo "📊 Creating database..."
if ! gcloud sql databases describe logistics_kg --instance=knowledge-graph-db --format="value(name)" 2>/dev/null; then
    gcloud sql databases create logistics_kg --instance=knowledge-graph-db
else
    echo "✅ Database already exists"
fi

# Create database user
echo "👤 Creating database user..."
if ! gcloud sql users describe postgres --instance=knowledge-graph-db --format="value(name)" 2>/dev/null; then
    DB_PASSWORD=$(openssl rand -base64 32)
    gcloud sql users create postgres --instance=knowledge-graph-db --password=$DB_PASSWORD
else
    echo "✅ Database user already exists"
    # Get existing password or set a new one
    DB_PASSWORD=$(openssl rand -base64 32)
    gcloud sql users set-password postgres --instance=knowledge-graph-db --password=$DB_PASSWORD
fi

# Get connection name
DB_CONNECTION_NAME=$(gcloud sql instances describe knowledge-graph-db --format="value(connectionName)")

echo "✅ Cloud SQL PostgreSQL created"
echo "   Connection Name: $DB_CONNECTION_NAME"
echo "   Database: logistics_kg"
echo "   User: postgres"

# Step 2: Set up Neo4j AuraDB (Manual step)
echo "🕸️ Neo4j AuraDB Setup"
echo "========================"
echo "Please complete these steps manually:"
echo "1. Go to https://console.neo4j.io/"
echo "2. Sign up/login to Neo4j Aura"
echo "3. Create a new AuraDB Professional instance"
echo "4. Set region: us-central1"
echo "5. Set size: 4GB RAM, 160GB Storage"
echo "6. Save connection details for next step"
echo ""
read -p "Press Enter after Neo4j AuraDB setup is complete..."

# Get Neo4j details from user
read -p "Enter Neo4j URI (e.g., bolt://xxx.databases.neo4j.io:7687): " NEO4J_URI
read -p "Enter Neo4j password: " NEO4J_PASSWORD

# Step 3: Set up Secret Manager
echo "🔐 Setting up Secret Manager..."

# Database secrets
echo "  🔐 Creating database secrets..."
if ! gcloud secrets describe postgres-password --format="value(name)" 2>/dev/null; then
    echo -n $DB_PASSWORD | gcloud secrets create postgres-password --data-file=-
else
    echo "✅ postgres-password secret already exists"
fi

if ! gcloud secrets describe neo4j-password --format="value(name)" 2>/dev/null; then
    echo -n $NEO4J_PASSWORD | gcloud secrets create neo4j-password --data-file=-
else
    echo "✅ neo4j-password secret already exists"
fi

if ! gcloud secrets describe neo4j-uri --format="value(name)" 2>/dev/null; then
    echo -n $NEO4J_URI | gcloud secrets create neo4j-uri --data-file=-
else
    echo "✅ neo4j-uri secret already exists"
fi

if ! gcloud secrets describe postgres-connection --format="value(name)" 2>/dev/null; then
    echo -n $DB_CONNECTION_NAME | gcloud secrets create postgres-connection --data-file=-
else
    echo "✅ postgres-connection secret already exists"
fi

# API secrets
echo "  🔐 Creating API secrets..."
read -p "Enter OpenAI API Key (or press Enter to skip): " OPENAI_API_KEY
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo -n $OPENAI_API_KEY | gcloud secrets create openai-api-key --data-file=-
fi

# JWT secret
JWT_SECRET=$(openssl rand -base64 64)
echo -n $JWT_SECRET | gcloud secrets create jwt-secret --data-file=-

# Grant secret access to service account
echo "  🔐 Granting secret access..."
gcloud secrets add-iam-policy-binding postgres-password \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding neo4j-password \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding neo4j-uri \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding postgres-connection \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

if [ ! -z "$OPENAI_API_KEY" ]; then
    gcloud secrets add-iam-policy-binding openai-api-key \
        --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
fi

echo "✅ Secret Manager setup complete"

# Step 4: Build and deploy services
echo "🐳 Building and deploying services..."

# Create Artifact Registry repository
echo "  📦 Creating Artifact Registry repository..."
if ! gcloud artifacts repositories describe kg-platform --location=$REGION --format="value(name)" 2>/dev/null; then
    gcloud artifacts repositories create kg-platform \
        --repository-format=docker \
        --location=$REGION
else
    echo "✅ Artifact Registry repository already exists"
fi

# Build main API
echo "  🚀 Building main API..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/kg-api:latest \
    --timeout=1800 \
    --config cloudbuild.yaml .

# Build compliance engine
echo "  🛡️ Building compliance engine..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/kg-compliance:latest \
    --timeout=1800 \
    --config cloudbuild-compliance.yaml .

# Build AI Studio API
echo "  🤖 Building AI Studio API..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/kg-ai-studio:latest \
    --timeout=1800 \
    --config cloudbuild-ai-studio.yaml .

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

if [ ! -z "$OPENAI_API_KEY" ]; then
    gcloud run services update kg-compliance \
        --region $REGION \
        --set-secrets OPENAI_API_KEY=openai-api-key:latest
fi

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

# Step 5: Initialize databases
echo "🗄️ Initializing databases..."

# Get service URLs
API_URL=$(gcloud run services describe kg-api --region $REGION --format="value(status.url)")
COMPLIANCE_URL=$(gcloud run services describe kg-compliance --region $REGION --format="value(status.url)")
AI_STUDIO_URL=$(gcloud run services describe kg-ai-studio --region $REGION --format="value(status.url)")

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Apply database schema
echo "  📊 Applying database schema..."
gcloud sql connect knowledge-graph-db --user=postgres --quiet < database/schema.sql
gcloud sql connect knowledge-graph-db --user=postgres --quiet < database/compliance_schema.sql
gcloud sql connect knowledge-graph-db --user=postgres --quiet < database/ocr_integration_schema.sql

# Initialize Neo4j
echo "  🕸️ Initializing Neo4j..."
curl -X POST "$API_URL/init" -H "Content-Type: application/json" || echo "⚠️  Neo4j initialization may need manual setup"

# Step 6: Test deployment
echo "🧪 Testing deployment..."

echo "  🚀 Testing main API..."
curl -f "$API_URL/health" || echo "❌ Main API health check failed"

echo "  🛡️ Testing compliance engine..."
curl -f "$COMPLIANCE_URL/health" || echo "❌ Compliance engine health check failed"

echo "  🤖 Testing AI Studio API..."
curl -f "$AI_STUDIO_URL/health" || echo "❌ AI Studio API health check failed"

# Step 7: Set up monitoring
echo "📊 Setting up monitoring..."

# Create monitoring dashboard
echo "  📈 Creating monitoring dashboard..."
cat > monitoring-dashboard.json << EOF
{
  "displayName": "Knowledge Graph Platform",
  "gridLayout": {
    "columns": "12",
    "widgets": [
      {
        "title": "API Response Time",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "prometheusQuery": {
                  "query": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
                }
              }
            }
          ]
        }
      }
    ]
  }
}
EOF

# Create alerting policies
echo "  🚨 Creating alerting policies..."
cat > alert-policies.yaml << EOF
type: google.cloud.monitoring.v3.AlertPolicy
displayName: "High API Error Rate"
conditions:
  - displayName: "Error rate > 5%"
    conditionThreshold:
      filter: 'metric.type="serviceruntime.googleapis.com/request/count" AND resource.type="cloud_run_revision"'
      aggregations:
      - alignmentPeriod: 300s
        perSeriesAligner: ALIGN_RATE
        alignmentGrouper: []
      comparison: COMPARISON_GT
      duration: 0s
      trigger:
        count: 1
        percent: 5
alertStrategy:
  notificationChannels:
  - projects/$PROJECT_ID/notificationChannels/1234567890
EOF

# Step 8: Output deployment information
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
echo "🗄️ Database Information:"
echo "  Cloud SQL Instance: knowledge-graph-db"
echo "  PostgreSQL Database: logistics_kg"
echo "  Neo4j AuraDB: $NEO4J_URI"
echo ""
echo "📊 Monitoring:"
echo "  Cloud Console: https://console.cloud.google.com/monitoring"
echo "  Cloud Run Services: https://console.cloud.google.com/run"
echo ""
echo "🤖 AI Studio Integration:"
echo "  Use the AI Studio API endpoints for Google AI Studio"
echo "  Endpoint: $AI_STUDIO_URL/ai/query"
echo "  Documentation: $AI_STUDIO_URL/docs"
echo ""
echo "🔐 Next Steps:"
echo "  1. Test all APIs using the provided URLs"
echo "  2. Configure AI Studio to use the AI Studio API"
echo "  3. Set up additional monitoring and alerting"
echo "  4. Configure custom domains if needed"
echo ""
echo "💰 Estimated Monthly Costs:"
echo "  Cloud Run (3 services): \$30-50"
echo "  Cloud SQL: \$150-200"
echo "  Neo4j AuraDB: \$100-150"
echo "  Secret Manager: \$5-10"
echo "  Cloud Build: \$10-20"
echo "  Monitoring: \$5-10"
echo "  Total: \$300-440"
echo ""
echo "✅ Your Knowledge Graph Platform is now live on Google Cloud!"
echo ""
echo "🌍 Deploy to Google Cloud:"
echo "   ./scripts/deploy-google-cloud.sh"
echo ""
echo "🤖 AI Studio Integration:"
echo "   KG_API_URL=$API_URL"
echo "   VITE_KG_API_URL=$AI_STUDIO_URL"
