# Google AI Studio Integration Guide

## 🎯 Overview

This guide shows how to integrate your Knowledge Graph Platform with Google AI Studio for enhanced AI capabilities.

## 🌐 AI Studio API Endpoints

### Main AI Studio API URL
```
https://kg-ai-studio-[hash].run.app
```

### Key Endpoints

#### 1. Natural Language Query
```bash
POST /ai/query
Content-Type: application/json

{
  "query": "Has 'GLOBAL TRADING COMPANY' sent 'INDUSTRIAL MACHINERY' to 'HAMBURG'?",
  "context": "Trade compliance check",
  "max_results": 10,
  "include_compliance": true
}
```

#### 2. Entity Extraction
```bash
POST /ai/extract-entities
Content-Type: application/json

{
  "text": "GLOBAL TRADING COMPANY LTD sent industrial machinery to Hamburg Port",
  "entity_types": ["LegalEntity", "Product", "Location"]
}
```

#### 3. AI Compliance Check
```bash
POST /ai/compliance-check
Content-Type: application/json

{
  "document_text": "Bill of Lading from GLOBAL TRADING COMPANY to HAMBURG PORT",
  "document_type": "bill_of_lading",
  "compliance_rules": ["IBAN_FORMAT", "ENTITY_SANCTION_LIST"]
}
```

#### 4. Graph Statistics
```bash
GET /ai/graph-stats
```

## 🔧 AI Studio Configuration

### Environment Variables for AI Studio
```bash
# AI Studio Configuration
KG_API_URL=https://kg-api-[hash].run.app
VITE_KG_API_URL=https://kg-ai-studio-[hash].run.app

# For AI Studio integration
AI_STUDIO_API_URL=https://kg-ai-studio-[hash].run.app
AI_STUDIO_API_KEY=your_api_key_here
```

### AI Studio Prompt Configuration

#### 1. Knowledge Graph Query Prompt
```
You are a logistics trade expert with access to a comprehensive knowledge graph. 
Use the provided API to answer questions about trade documents, entities, and relationships.

Available endpoints:
- POST /ai/query - Natural language queries
- POST /ai/extract-entities - Extract entities from text
- POST /ai/compliance-check - Check compliance
- GET /ai/graph-stats - Get graph statistics

Example queries:
- "How many documents involve 'GLOBAL TRADING COMPANY'?"
- "What products have been shipped to 'HAMBURG PORT'?"
- "Check compliance for this document: [document text]"
```

#### 2. Compliance Analysis Prompt
```
You are a trade compliance expert. Use the Knowledge Graph compliance engine to analyze documents for compliance issues.

Process:
1. Extract entities from the document
2. Run compliance checks
3. Analyze risk factors
4. Provide recommendations

Available compliance rules:
- IBAN validation
- Sanctions screening
- Trade restrictions
- Entity verification
```

## 🚀 Quick Start with AI Studio

### 1. Set Up AI Studio
```bash
# Get your AI Studio API URL
AI_STUDIO_URL=$(gcloud run services describe kg-ai-studio --region us-central1 --format="value(status.url)")

# Test the API
curl -X POST "$AI_STUDIO_URL/ai/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many customers do we have?"}'
```

### 2. Configure AI Studio Integration
```javascript
// AI Studio integration example
const AI_STUDIO_API_URL = "https://kg-ai-studio-[hash].run.app";

async function queryKnowledgeGraph(query) {
  const response = await fetch(`${AI_STUDIO_API_URL}/ai/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      include_compliance: true,
      max_results: 10
    })
  });
  
  return await response.json();
}

// Example usage
const result = await queryKnowledgeGraph(
  "Has 'GLOBAL TRADING COMPANY' sent 'INDUSTRIAL MACHINERY' to 'HAMBURG'?"
);
```

### 3. AI Studio Custom Functions
```python
# Custom function for AI Studio
def analyze_trade_document(document_text):
    """Analyze trade document using Knowledge Graph AI"""
    
    # Extract entities
    entities = extract_entities_from_text(document_text)
    
    # Check compliance
    compliance_result = check_compliance(document_text)
    
    # Query related information
    related_info = query_knowledge_graph(
        f"Show documents involving {entities.get('companies', [])}"
    )
    
    return {
        "entities": entities,
        "compliance": compliance_result,
        "related_documents": related_info,
        "recommendations": generate_recommendations(compliance_result)
    }
```

## 📊 AI Studio Use Cases

### 1. Document Analysis
```
Input: Trade document text
Process: Extract entities → Check compliance → Find related documents
Output: Complete analysis with risk assessment
```

### 2. Relationship Discovery
```
Input: Entity names
Process: Query graph → Find relationships → Analyze patterns
Output: Relationship map with confidence scores
```

### 3. Compliance Monitoring
```
Input: Document or transaction
Process: Run compliance rules → Calculate risk → Generate alerts
Output: Compliance report with recommendations
```

### 4. Market Intelligence
```
Input: Market query
Process: Query graph → Analyze trends → Generate insights
Output: Market analysis with data visualization
```

## 🔍 Advanced AI Studio Features

### 1. Multi-Modal Analysis
```javascript
// Combine text analysis with graph queries
async function comprehensiveAnalysis(document) {
  const [entities, relationships, compliance] = await Promise.all([
    extractEntities(document.text),
    findRelationships(document.entities),
    checkCompliance(document.text)
  ]);
  
  return {
    entities,
    relationships,
    compliance,
    insights: generateInsights(entities, relationships, compliance)
  };
}
```

### 2. Real-time Monitoring
```javascript
// Set up real-time compliance monitoring
const monitor = setInterval(async () => {
  const newDocuments = await getNewDocuments();
  
  for (const doc of newDocuments) {
    const compliance = await checkCompliance(doc.text);
    if (compliance.risk_score > 0.7) {
      await sendAlert(doc, compliance);
    }
  }
}, 60000); // Check every minute
```

### 3. Predictive Analytics
```javascript
// Predict potential compliance issues
async function predictComplianceRisk(entity, transaction) {
  const historicalData = await getEntityHistory(entity);
  const riskFactors = analyzeRiskFactors(historicalData);
  const prediction = predictRisk(riskFactors, transaction);
  
  return {
    risk_score: prediction.score,
    risk_factors: riskFactors,
    recommendations: prediction.recommendations
  };
}
```

## 🎯 Best Practices

### 1. API Usage
- Use batch operations for multiple queries
- Implement caching for frequently accessed data
- Handle rate limits and errors gracefully
- Use appropriate timeouts for API calls

### 2. Security
- Never expose API keys in client-side code
- Use authentication for sensitive operations
- Implement proper error handling
- Log API usage for monitoring

### 3. Performance
- Optimize query complexity
- Use pagination for large result sets
- Implement lazy loading for complex data
- Monitor API response times

## 🔧 Troubleshooting

### Common Issues
1. **API Timeouts**: Increase timeout values or optimize queries
2. **Authentication Errors**: Check API keys and permissions
3. **Rate Limiting**: Implement exponential backoff
4. **Data Inconsistency**: Verify database synchronization

### Debug Tools
```bash
# Check API health
curl -f "$AI_STUDIO_URL/health"

# Test specific endpoint
curl -X POST "$AI_STUDIO_URL/ai/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'

# View logs
gcloud logs read "resource.type=cloud_run_revision" \
  --limit 50 \
  --format="table(textPayload)"
```

## 🚀 Next Steps

1. **Custom AI Models**: Train custom models for your specific domain
2. **Advanced Analytics**: Implement predictive analytics and forecasting
3. **Integration**: Connect with other business systems
4. **Monitoring**: Set up comprehensive monitoring and alerting
5. **Optimization**: Continuously optimize performance and accuracy

---

## 🎉 Ready for AI Studio!

Your Knowledge Graph Platform is now deployed on Google Cloud and ready for AI Studio integration:

**🌐 AI Studio API**: `https://kg-ai-studio-[hash].run.app`
**📚 Documentation**: `https://kg-ai-studio-[hash].run.app/docs`
**🔧 Environment Variables**: `KG_API_URL` and `VITE_KG_API_URL`

Start building intelligent AI applications with your knowledge graph! 🚀🤖
