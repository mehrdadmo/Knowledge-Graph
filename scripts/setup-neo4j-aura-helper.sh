#!/bin/bash

# Neo4j AuraDB Setup Helper
set -e

echo "🕸️ Neo4j AuraDB Setup Helper"
echo "=============================="
echo ""
echo "1. Go to: https://console.neo4j.io/"
echo "2. Login or create account"
echo "3. Click 'Create Database' → 'AuraDB Professional'"
echo "4. Configure:"
echo "   - Database Name: knowledge-graph-db"
echo "   - Region: us-central1"
echo "   - Size: 4GB RAM, 160GB Storage"
echo "   - Plan: Professional"
echo ""
echo "5. After creation, save these details:"
echo ""

# Prompt for Neo4j details
read -p "Enter Neo4j URI (e.g., bolt://xxx.databases.neo4j.io:7687): " NEO4J_URI
read -p "Enter Neo4j password: " NEO4J_PASSWORD

# Validate inputs
if [ -z "$NEO4J_URI" ]; then
    echo "❌ Neo4j URI is required"
    exit 1
fi

if [ -z "$NEO4J_PASSWORD" ]; then
    echo "❌ Neo4j password is required"
    exit 1
fi

echo ""
echo "✅ Neo4j details captured:"
echo "   URI: $NEO4J_URI"
echo "   Password: [hidden]"
echo ""

# Save to secrets
export PATH="/Users/mehrdadmohamadali/Desktop/Knowledge Graph/google-cloud-sdk/google-cloud-sdk/bin:$PATH"
PROJECT_ID="knowledge-graph-1771880019"

echo "🔐 Saving to Google Secret Manager..."

# Create secrets
echo -n $NEO4J_URI | gcloud secrets create neo4j-uri --data-file=-
echo -n $NEO4J_PASSWORD | gcloud secrets create neo4j-password --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding neo4j-uri \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding neo4j-password \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

echo "✅ Neo4j secrets saved to Google Cloud"
echo ""
echo "🚀 Ready to continue with deployment!"
echo "Run: ./scripts/deploy-google-cloud-complete.sh"
