# 🚀 Google Cloud Deployment Guide

## 📋 Quick Deployment

### **Option 1: Automated Deployment (Recommended)**

```bash
# Run the complete deployment script
cd "/Users/mehrdadmohamadali/Desktop/Knowledge Graph"
./scripts/deploy-google-cloud-complete.sh
```

### **Option 2: Manual Step-by-Step**

#### **Step 1: Set Up Google Cloud**
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Authenticate
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project knowledge-graph-platform
```

#### **Step 2: Enable APIs**
```bash
gcloud services enable run.googleapis.com
gcloud services enable sql-component.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

#### **Step 3: Create Databases**

**Cloud SQL PostgreSQL:**
```bash
gcloud sql instances create knowledge-graph-db \
    --database-version=POSTGRES_15 \
    --tier=db-custom-4-16384 \
    --region=us-central1 \
    --storage-size=100GB \
    --storage-type=SSD

gcloud sql databases create logistics_kg --instance=knowledge-graph-db
```

**Neo4j AuraDB:**
1. Go to https://console.neo4j.io/
2. Create AuraDB Professional instance
3. Save connection details

#### **Step 4: Set Up Secrets**
```bash
# Create secrets for credentials
echo -n "your_password" | gcloud secrets create postgres-password --data-file=-
echo -n "your_neo4j_password" | gcloud secrets create neo4j-password --data-file=-
echo -n "bolt://xxx.databases.neo4j.io:7687" | gcloud secrets create neo4j-uri --data-file=-
```

#### **Step 5: Deploy Services**
```bash
# Build and deploy main API
gcloud builds submit --tag gcr.io/knowledge-graph-platform/kg-api:latest .
gcloud run deploy kg-api --image gcr.io/knowledge-graph-platform/kg-api:latest \
    --region us-central1 --allow-unauthenticated --memory 1Gi

# Build and deploy compliance engine
gcloud builds submit --tag gcr.io/knowledge-graph-platform/kg-compliance:latest \
    --config cloudbuild-compliance.yaml .
gcloud run deploy kg-compliance --image gcr.io/knowledge-graph-platform/kg-compliance:latest \
    --region us-central1 --allow-unauthenticated --memory 1Gi

# Build and deploy AI Studio API
gcloud builds submit --tag gcr.io/knowledge-graph-platform/kg-ai-studio:latest \
    --config cloudbuild-ai-studio.yaml .
gcloud run deploy kg-ai-studio --image gcr.io/knowledge-graph-platform/kg-ai-studio:latest \
    --region us-central1 --allow-unauthenticated --memory 1Gi
```

## 🌐 Access URLs After Deployment

| Service | URL | Description |
|---------|-----|-------------|
| **Main API** | `https://kg-api-xxxxx-uc.a.run.app` | GraphRAG queries |
| **Compliance API** | `https://kg-compliance-xxxxx-uc.a.run.app` | Compliance checking |
| **AI Studio API** | `https://kg-ai-studio-xxxxx-uc.a.run.app` | AI Studio integration |
| **API Docs** | `https://kg-api-xxxxx-uc.a.run.app/docs` | Interactive docs |

## 🔧 Environment Variables

For AI Studio integration:
```bash
KG_API_URL=https://kg-api-xxxxx-uc.a.run.app
VITE_KG_API_URL=https://kg-ai-studio-xxxxx-uc.a.run.app
```

## 💰 Cost Estimates

| Service | Configuration | Monthly Cost |
|---------|---------------|---------------|
| **Cloud Run** | 3 services × 1Gi RAM | $30-50 |
| **Cloud SQL** | 4CPU, 16GB RAM, 100GB SSD | $150-200 |
| **Neo4j AuraDB** | 4GB RAM, 160GB Storage | $100-150 |
| **Secret Manager** | API calls | $5-10 |
| **Cloud Build** | Builds | $10-20 |
| **Monitoring** | Basic metrics | $5-10 |
| **Total** | | **$300-440** |

## 🧪 Testing Deployment

```bash
# Test health endpoints
curl https://kg-api-xxxxx-uc.a.run.app/health
curl https://kg-compliance-xxxxx-uc.a.run.app/health
curl https://kg-ai-studio-xxxxx-uc.a.run.app/health

# Test API functionality
curl -X POST https://kg-api-xxxxx-uc.a.run.app/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many customers do we have?"}'
```

## 🤖 AI Studio Integration

### **1. Set Up AI Studio**
```bash
# Configure AI Studio to use your deployed API
export KG_API_URL=https://kg-api-xxxxx-uc.a.run.app
export VITE_KG_API_URL=https://kg-ai-studio-xxxxx-uc.a.run.app
```

### **2. Test AI Studio Endpoints**
```bash
# Natural language query
curl -X POST https://kg-ai-studio-xxxxx-uc.a.run.app/ai/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all documents from GLOBAL TRADING COMPANY"}'

# Entity extraction
curl -X POST https://kg-ai-studio-xxxxx-uc.a.run.app/ai/extract-entities \
  -H "Content-Type: application/json" \
  -d '{"text": "GLOBAL TRADING COMPANY shipped industrial machinery to Hamburg"}'

# AI compliance check
curl -X POST https://kg-ai-studio-xxxxx-uc.a.run.app/ai/compliance-check \
  -H "Content-Type: application/json" \
  -d '{"document_text": "Bill of Lading from GLOBAL TRADING COMPANY"}'
```

## 🔍 Monitoring

### **Cloud Console**
- **Monitoring**: https://console.cloud.google.com/monitoring
- **Cloud Run**: https://console.cloud.google.com/run
- **Cloud SQL**: https://console.cloud.google.com/sql
- **Secret Manager**: https://console.cloud.google.com/security/secret-manager

### **Key Metrics**
- API response times
- Error rates
- Request counts
- Database performance
- Memory usage

## 🛠️ Troubleshooting

### **Common Issues**

**1. Service Not Starting**
```bash
# Check logs
gcloud logs read "resource.type=cloud_run_revision" --limit 50

# Check service status
gcloud run services describe kg-api --region us-central1
```

**2. Database Connection Issues**
```bash
# Check Cloud SQL status
gcloud sql instances describe knowledge-graph-db

# Test connection
gcloud sql connect knowledge-graph-db --user=postgres
```

**3. Permission Errors**
```bash
# Check service account permissions
gcloud projects get-iam-policy knowledge-graph-platform

# Grant additional permissions
gcloud projects add-iam-policy-binding knowledge-graph-platform \
    --member="serviceAccount:kg-platform-sa@knowledge-graph-platform.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"
```

## 🎯 Production Checklist

- [ ] All services deployed and healthy
- [ ] Database schemas applied
- [ ] Monitoring configured
- [ ] Alert policies set
- [ ] Custom domains configured (optional)
- [ ] SSL certificates configured (optional)
- [ ] Backup strategies verified
- [ ] Load testing completed
- [ ] Security scan performed

## 🚀 Next Steps

1. **Custom Domain**: Configure custom domains for APIs
2. **CDN Setup**: Add Cloud CDN for better performance
3. **Load Testing**: Test with realistic traffic
4. **Security Hardening**: Implement additional security measures
5. **Scaling**: Configure auto-scaling policies
6. **Analytics**: Set up detailed analytics and reporting

---

## 🎉 Ready for Production!

Your Knowledge Graph Platform is now deployed on Google Cloud and ready for AI Studio integration!

**🌐 Main API**: `https://kg-api-xxxxx-uc.a.run.app`
**🤖 AI Studio API**: `https://kg-ai-studio-xxxxx-uc.a.run.app`
**📚 Documentation**: Available at `/docs` endpoints
**🔧 Environment**: `KG_API_URL` and `VITE_KG_API_URL`

**Start building intelligent AI applications with your knowledge graph!** 🚀🤖☁️
