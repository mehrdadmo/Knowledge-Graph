#!/bin/bash

# Cloud SQL PostgreSQL Setup
PROJECT_ID="knowledge-graph-platform"
REGION="us-central1"
DB_NAME="knowledge_graph_db"
DB_USER="postgres"
DB_PASSWORD="your_secure_password_here"

# Create Cloud SQL instance
gcloud sql instances create $DB_NAME \
    --database-version=POSTGRES_15 \
    --tier=db-custom-4-16384 \
    --region=$REGION \
    --storage-size=100GB \
    --storage-type=SSD \
    --backup-start-time=02:00 \
    --retained-backups-count=7 \
    --deletion-protection

# Create database
gcloud sql databases create logistics_kg \
    --instance=$DB_NAME

# Create user
gcloud sql users create $DB_USER \
    --instance=$DB_NAME \
    --password=$DB_PASSWORD

# Get connection details
DB_CONNECTION_NAME=$(gcloud sql instances describe $DB_NAME \
    --format="value(connectionName)")

echo "Cloud SQL Setup Complete!"
echo "Connection Name: $DB_CONNECTION_NAME"
echo "Database: logistics_kg"
echo "User: $DB_USER"
