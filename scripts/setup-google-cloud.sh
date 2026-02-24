#!/bin/bash

# Google Cloud Setup Script (After Billing is Enabled)
set -e

# Set project
export PROJECT_ID="knowledge-graph-1771880019"
export PATH="/Users/mehrdadmohamadali/Desktop/Knowledge Graph/google-cloud-sdk/google-cloud-sdk/bin:$PATH"

echo "🚀 Setting up Google Cloud Project: $PROJECT_ID"

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable sql-component.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable monitoring.googleapis.com

# Create service account
echo "🔐 Creating service account..."
gcloud iam service-accounts create kg-platform-sa \
    --display-name="Knowledge Graph Platform Service Account" \
    --description="Service account for Knowledge Graph Platform"

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

# Create Artifact Registry repository
echo "📦 Creating Artifact Registry repository..."
gcloud artifacts repositories create kg-platform \
    --repository-format=docker \
    --location=us-central1

echo "✅ Google Cloud setup complete!"
echo ""
echo "Next steps:"
echo "1. Enable billing in Google Cloud Console"
echo "2. Run: ./scripts/setup-databases.sh"
echo "3. Run: ./scripts/deploy-services.sh"
