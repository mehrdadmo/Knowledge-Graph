# 🛡️ Compliance Engine for Knowledge Graph

## 📋 Overview

The **Compliance Engine** provides automated compliance checking for trade documents using your knowledge graph intelligence. It validates IBANs, screens for sanctions, checks trade restrictions, and ensures regulatory compliance.

## 🚀 **Compliance Pipeline**

```
📄 Document → 🕸️ Graph Query → 🛡️ Compliance Rules → ✅/❌ Results → 📊 Report → 🚨 Alerts
```

## 🎯 **Key Features**

### **✅ Financial Compliance**
- **IBAN Validation**: Format and checksum validation
- **Country Sanctions**: Check IBAN countries against sanctions lists
- **Tax ID Validation**: Validate tax identification numbers
- **Amount Thresholds**: Check transaction reporting limits

### **✅ Sanctions Screening**
- **Entity Screening**: Screen companies against sanctions lists
- **Watchlist Monitoring**: Check against various watchlists
- **Country Embargoes**: Identify embargoed countries
- **Real-time Updates**: Automatic sanctions list updates

### **✅ Trade Compliance**
- **HS Code Restrictions**: Check for restricted goods
- **Dual-Use Goods**: Identify dual-use items
- **Export Controls**: Validate export compliance
- **Import Regulations**: Check import restrictions

### **✅ Document Validation**
- **Required Fields**: Ensure mandatory fields present
- **Date Consistency**: Validate date relationships
- **Format Validation**: Check data formats
- **Completeness**: Verify document completeness

## 🛠️ **Architecture Components**

### **1. Compliance Engine Core** (`backend/compliance_engine.py`)
- Main compliance checking logic
- Rule management and execution
- Report generation
- Integration with knowledge graph

### **2. Database Schema** (`database/compliance_schema.sql`)
- Compliance rules storage
- Reports and results tracking
- Sanctions lists management
- Alert system

### **3. REST API** (`backend/compliance_api.py`)
- FastAPI endpoints for compliance checking
- Real-time compliance monitoring
- Dashboard and analytics
- Alert management

### **4. Test Suite** (`samples/test_compliance_engine.py`)
- Comprehensive testing framework
- Performance validation
- Integration testing
- Interactive test mode

## 🚀 **Quick Start**

### **1. Start All Services**
```bash
./docker-manage.sh start
```

### **2. Initialize Compliance Database**
```bash
# Apply compliance schema
docker-compose exec postgres psql -U postgres -d logistics_kg -f /docker-entrypoint-initdb.d/compliance_schema.sql
```

### **3. Test Compliance Engine**
```bash
./docker-manage.sh compliance-test
```

### **4. Check Document Compliance**
```bash
./docker-manage.sh compliance-check 12345
```

### **5. Validate IBAN**
```bash
./docker-manage.sh compliance-iban "DE89370400440532013000"
```

## 📊 **Compliance Commands**

### **Document Checking**
```bash
# Check specific document
./docker-manage.sh compliance-check <document_id>

# Batch check documents
curl -X POST http://localhost:8001/compliance/batch-check \
  -H "Content-Type: application/json" \
  -d '{"document_ids": [123, 124, 125]}'
```

### **Validation Tools**
```bash
# Validate IBAN
./docker-manage.sh compliance-iban <iban>

# List compliance rules
./docker-manage.sh compliance-rules

# Show compliance dashboard
./docker-manage.sh compliance-dashboard
```

### **Testing & Monitoring**
```bash
# Test all compliance functions
./docker-manage.sh compliance-test

# View compliance logs
./docker-manage.sh logs kg_compliance

# Check API health
curl http://localhost:8001/health
```

## 🛡️ **Compliance Rules**

### **Financial Rules**
- **IBAN_FORMAT**: Validate IBAN format and checksum
- **IBAN_COUNTRY_SANCTION**: Check IBAN country sanctions
- **TAX_ID_VALIDATION**: Validate tax identification numbers
- **AMOUNT_THRESHOLD**: Check transaction reporting limits

### **Sanctions Rules**
- **ENTITY_SANCTION_LIST**: Screen entities against sanctions
- **WATCHLIST_SCREENING**: Check against watchlists
- **EMBARGO_COUNTRY**: Identify embargoed countries

### **Trade Rules**
- **HS_CODE_RESTRICTION**: Check HS code restrictions
- **DUAL_USE_GOODS**: Identify dual-use goods
- **EXPORT_CONTROLS**: Validate export compliance

### **Document Rules**
- **REQUIRED_FIELDS**: Ensure mandatory fields present
- **DATE_CONSISTENCY**: Validate date relationships
- **CURRENCY_VALIDATION**: Check ISO currency codes

## 📈 **Compliance Status Levels**

### **🟢 COMPLIANT**
- No violations found
- All checks passed
- Document ready for processing

### **🟡 WARNING**
- Minor issues found
- Review recommended
- Document may proceed with caution

### **🔴 NON_COMPLIANT**
- Critical violations found
- Document blocked
- Immediate action required

### **🟠 PENDING_REVIEW**
- Manual review needed
- Complex cases
- Expert assessment required

## 🚨 **Alert System**

### **Alert Types**
- **COMPLIANCE_VIOLATION**: Critical compliance issues
- **SANCTION_MATCH**: Sanctioned entity detected
- **RESTRICTED_GOODS**: Prohibited items found
- **FORMAT_ERROR**: Data format issues

### **Alert Severity**
- **CRITICAL**: Immediate action required
- **HIGH**: Urgent attention needed
- **MEDIUM**: Review recommended
- **LOW**: Informational only

### **Alert Management**
```bash
# View alerts
curl http://localhost:8001/compliance/alerts

# Acknowledge alert
curl -X PUT http://localhost:8001/compliance/alerts/123/acknowledge

# Resolve alert
curl -X PUT http://localhost:8001/compliance/alerts/123/resolve \
  -d '{"resolution_note": "False positive"}'
```

## 🕸️ **Knowledge Graph Integration**

### **Entity Extraction**
```cypher
// Get document entities for compliance checking
MATCH (d:Document {id: $document_id})
OPTIONAL MATCH (d)-[r]->(entity)
RETURN d, type(r) as relationship, entity.name, labels(entity)
```

### **Relationship Analysis**
```cypher
// Check entity relationships for compliance
MATCH (entity:LegalEntity)-[r]->(related)
WHERE entity.name CONTAINS $search_term
RETURN type(r), related.name, related.country
```

### **Pattern Detection**
```cypher
// Detect suspicious patterns
MATCH (doc:Document)-[:HAS_SHIPPER]->(shipper:LegalEntity)
WHERE shipper.country IN $sanctioned_countries
RETURN doc.id, shipper.name, shipper.country
```

## 📊 **API Endpoints**

### **Compliance Checking**
```bash
# Check single document
POST /compliance/check
{
  "document_id": 12345,
  "force_recheck": false
}

# Batch check documents
POST /compliance/batch-check
{
  "document_ids": [123, 124, 125]
}
```

### **Validation Tools**
```bash
# Validate IBAN
POST /validation/iban
{
  "iban": "DE89370400440532013000"
}

# Get compliance rules
GET /compliance/rules
```

### **Monitoring & Analytics**
```bash
# Compliance statistics
GET /compliance/statistics

# Compliance dashboard
GET /compliance/dashboard

# Compliance alerts
GET /compliance/alerts
```

## 🧪 **Testing Framework**

### **Test Categories**
1. **IBAN Validation**: Format and checksum testing
2. **Sanctions Checking**: Entity and IBAN sanctions
3. **Trade Compliance**: HS codes and restrictions
4. **Document Compliance**: Complete document checking
5. **Rule Management**: Rule configuration testing
6. **Graph Integration**: Knowledge graph connectivity
7. **Performance**: Speed and efficiency testing

### **Running Tests**
```bash
# Run all tests
./docker-manage.sh compliance-test

# Interactive test mode
docker-compose exec kg_compliance python ../samples/test_compliance_engine.py --interactive

# Specific test categories
docker-compose exec kg_compliance python ../samples/test_compliance_engine.py --test-iban
docker-compose exec kg_compliance python ../samples/test_compliance_engine.py --test-sanctions
docker-compose exec kg_compliance python ../samples/test_compliance_engine.py --test-trade
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Compliance Engine Settings
COMPLIANCE_DB_HOST=localhost
COMPLIANCE_DB_PORT=5432
COMPLIANCE_DB_NAME=logistics_kg
COMPLIANCE_LOG_LEVEL=INFO

# External Data Sources
SANCTIONS_API_KEY=your_api_key
SANCTIONS_UPDATE_INTERVAL=3600
WATCHLIST_API_URL=https://api.watchlist.com
```

### **Rule Configuration**
```python
# Enable/disable specific rules
compliance_engine.rules['IBAN_FORMAT'].enabled = True
compliance_engine.rules['ENTITY_SANCTION_LIST'].enabled = True

# Adjust rule parameters
compliance_engine.rules['AMOUNT_THRESHOLD'].parameters = {
    'threshold_usd': 10000,
    'threshold_eur': 8500
}
```

## 📈 **Performance Metrics**

### **Expected Performance**
- **IBAN Validation**: <1ms per validation
- **Document Check**: <500ms per document
- **Sanctions Screening**: <200ms per entity
- **Batch Processing**: 100+ documents/second

### **Monitoring**
```bash
# Check API performance
curl -w "@curl-format.txt" http://localhost:8001/health

# Monitor compliance queue
curl http://localhost:8001/compliance/statistics

# View system metrics
docker stats kg_compliance
```

## 🌐 **Access Points**

### **API Endpoints**
- **Compliance API**: `http://localhost:8001`
- **API Documentation**: `http://localhost:8001/docs`
- **Health Check**: `http://localhost:8001/health`

### **Management Interface**
- **Compliance Dashboard**: `http://localhost:8001/compliance/dashboard`
- **Alert Management**: `http://localhost:8001/compliance/alerts`
- **Rule Management**: `http://localhost:8001/compliance/rules`

## 🔍 **Use Cases**

### **1. Trade Document Processing**
- Automatic compliance checking on document upload
- Real-time violation detection
- Automated approval/rejection workflows

### **2. Sanctions Screening**
- Continuous entity monitoring
- Real-time sanctions list updates
- Automated alert generation

### **3. Risk Assessment**
- Document risk scoring
- Entity relationship analysis
- Pattern detection and prediction

### **4. Regulatory Reporting**
- Automated compliance reporting
- Audit trail generation
- Regulatory submission preparation

## 🚨 **Troubleshooting**

### **Common Issues**
1. **False Positives**: Adjust rule parameters
2. **Performance Issues**: Check database connections
3. **Missing Data**: Verify graph integration
4. **API Errors**: Check service status

### **Debug Commands**
```bash
# Check service status
./docker-manage.sh status

# View detailed logs
./docker-manage.sh logs kg_compliance

# Test database connection
docker-compose exec kg_compliance python -c "from neo4j_manager import Neo4jManager; print(Neo4jManager().get_graph_statistics())"

# Validate configuration
curl http://localhost:8001/health
```

## 🎯 **Best Practices**

### **1. Rule Management**
- Regularly review and update rules
- Monitor false positive rates
- Adjust parameters based on business needs

### **2. Performance Optimization**
- Cache frequently used data
- Batch process when possible
- Monitor system resources

### **3. Data Quality**
- Ensure accurate entity extraction
- Maintain up-to-date sanctions lists
- Validate data formats

### **4. Alert Management**
- Set appropriate alert thresholds
- Establish clear escalation procedures
- Regularly review and resolve alerts

## 🚀 **Future Enhancements**

### **Planned Features**
- **Machine Learning**: AI-based pattern recognition
- **Advanced Analytics**: Predictive compliance scoring
- **Multi-Language Support**: International compliance
- **Blockchain Integration**: Immutable audit trails

### **Integration Opportunities**
- **External APIs**: Real-time sanctions data
- **Regulatory Systems**: Government reporting
- **Third-party Tools**: Industry compliance platforms
- **Custom Workflows**: Business process integration

---

## 🎉 **Your Compliance Engine is Ready!**

**You now have a comprehensive compliance system that:**

- ✅ **Automatically validates** IBANs, IDs, and financial data
- ✅ **Screens entities** against sanctions lists in real-time
- ✅ **Checks trade compliance** for HS codes and restrictions
- ✅ **Generates alerts** for compliance violations
- ✅ **Integrates with** your knowledge graph intelligence
- ✅ **Provides detailed reports** and analytics
- ✅ **Scales to handle** thousands of documents

**Your documents are now automatically checked for compliance with real-time alerts and detailed reporting!** 🛡️⚡🎯
