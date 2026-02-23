#!/bin/bash

# Google Cloud Secret Manager Setup
PROJECT_ID="knowledge-graph-platform"

echo "=== Setting up Google Cloud Secret Manager ==="

# Database secrets
echo "Creating database secrets..."
gcloud secrets create postgres-password --replication-policy=automatic
echo -n "your_secure_postgres_password" | gcloud secrets versions add postgres-password --data-file=-

gcloud secrets create neo4j-password --replication-policy=automatic
echo -n "your_secure_neo4j_password" | gcloud secrets versions add neo4j-password --data-file=-

# API secrets
gcloud secrets create openai-api-key --replication-policy=automatic
echo -n "sk-your-openai-api-key" | gcloud secrets versions add openai-api-key --data-file=-

# Connection strings
gcloud secrets create neo4j-uri --replication-policy=automatic
echo -n "bolt://xxx.databases.neo4j.io:7687" | gcloud secrets versions add neo4j-uri --data-file=-

gcloud secrets create postgres-connection --replication-policy=automatic
echo -n "your-project:us-central1:knowledge_graph_db" | gcloud secrets versions add postgres-connection --data-file=-

# Application secrets
gcloud secrets create jwt-secret --replication-policy=automatic
echo -n "your_jwt_secret_key_here" | gcloud secrets versions add jwt-secret --data-file=-

echo "=== Secrets created successfully ==="
echo ""
echo "Grant Cloud Run access to secrets:"
gcloud secrets add-iam-policy-binding postgres-password \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding neo4j-password \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:kg-platform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

echo "=== Secret access granted to Cloud Run service account ==="
