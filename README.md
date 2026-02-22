# Logistics Knowledge Graph

A comprehensive knowledge graph solution for the logistics and trade industry that transforms fragmented SQL data into connected graph relationships for enhanced analysis and insights.

## 🚀 Overview

This system bridges traditional relational databases with graph databases to create a unified view of logistics entities and their relationships. It features **real-time CDC (Change Data Capture)** and **GraphRAG (Graph Retrieval Augmented Generation)** capabilities for intelligent natural language querying.

### Key Features

- **🔄 Real-time CDC**: Automatic sync when `hitl_finished_at` is updated via PostgreSQL triggers
- **🤖 GraphRAG API**: Natural language to Cypher query translation with FastAPI
- **📊 Intelligent Analytics**: Pre-built query patterns for supply chain analysis
- **🐳 Dockerized Deployment**: Complete containerized setup with all services
- **⚡ High Performance**: Async processing and optimized graph queries
- **🎯 Risk Assessment**: Automated entity risk analysis based on graph patterns

## 📊 Architecture

### Data Flow

```
Document Processing → PostgreSQL → [CDC Trigger] → Real-time Sync → Neo4j Knowledge Graph → GraphRAG API → LLM/SLM
```

### Services Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Neo4j       │    │   FastAPI       │
│   (Source DB)   │◄──►│   (Graph DB)    │◄──►│   (GraphRAG)    │
│                 │    │                 │    │                 │
│ • CDC Triggers  │    │ • Relationships │    │ • NL to Cypher  │
│ • Notifications │    │ • Constraints   │    │ • API Endpoints │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Real-time Sync  │
                    │   Service       │
                    │                 │
                    │ • Listens CDC   │
                    │ • Auto Sync     │
                    └─────────────────┘
```

### Graph Schema

The knowledge graph models logistics entities and their relationships:

- **Customer** → **PROCESSED** → **Document**
- **Document** → **HAS_SHIPPER** → **LegalEntity**
- **Document** → **HAS_CONSIGNEE** → **LegalEntity**
- **Document** → **CONTAINS** → **Product**
- **Product** → **CLASSIFIED_AS** → **HSCode**
- **Document** → **ORIGINATED_FROM** → **Location**
- **Document** → **DESTINED_FOR** → **Location**

### SQL to Graph Mapping

| SQL Table/Column | Graph Node Label | Purpose |
|------------------|------------------|---------|
| Customer | Customer | Logistics firm using the system |
| Document | Document | Specific document instance |
| DocumentField (ShipperName) | LegalEntity | Company sending goods |
| DocumentField (HS_Code) | HSCode | Regulatory classification |
| DocumentField (Product) | Product | Item being traded |
| DocumentField (OriginPort) | Location | Port of origin |
| DocumentField (DestinationPort) | Location | Port of destination |

## 🛠️ Quick Start

### Prerequisites

- Docker and Docker Compose
- Git (for cloning)

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd "Knowledge Graph"
```

2. **Start all services**:
```bash
./docker-manage.sh start
```

3. **Initialize the knowledge graph**:
```bash
./docker-manage.sh init
```

4. **Sync sample data**:
```bash
./docker-manage.sh sync
```

5. **Verify setup**:
```bash
./docker-manage.sh test
./docker-manage.sh sync-status
```

### Access Points

- **PostgreSQL**: `localhost:5432`
- **Neo4j HTTP**: `http://localhost:7474`
- **Neo4j Bolt**: `bolt://localhost:7687`
- **🤖 GraphRAG API**: `http://localhost:8000`
- **📚 API Documentation**: `http://localhost:8000/docs`
- **🔍 Neo4j Browser** (optional): `http://localhost:7475`

## 📁 Project Structure

```
Knowledge Graph/
├── backend/                    # Python application
│   ├── config.py              # Configuration management
│   ├── database_manager.py    # PostgreSQL operations
│   ├── neo4j_manager.py       # Neo4j operations
│   ├── knowledge_graph_sync.py # Main sync logic
│   ├── api.py                 # 🤖 FastAPI GraphRAG service
│   ├── nl_to_cypher.py        # Natural language to Cypher translator
│   ├── realtime_sync.py       # 🔄 Real-time CDC listener
│   ├── schemas.py             # Pydantic data models
│   ├── cli.py                 # Command-line interface
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Python service container
├── database/                  # SQL schemas and data
│   ├── schema.sql             # Database schema with CDC triggers
│   └── sample_data.sql        # Sample data
├── samples/                   # Testing and examples
│   ├── test_suite.py          # Comprehensive tests
│   ├── query_examples.py      # Sample Cypher queries
│   ├── test_graphrag_api.py   # 🤖 GraphRAG API tests
│   └── interactive_query.py   # 🎯 Interactive query client
├── docker/                    # Docker configurations
├── docker-compose.yml         # Multi-container setup
├── docker-manage.sh          # Management script
└── README.md                  # This file
```

## 🔧 Management Commands

The `docker-manage.sh` script provides easy management:

```bash
# Service Management
./docker-manage.sh start          # Start all services
./docker-manage.sh stop           # Stop all services
./docker-manage.sh restart        # Restart all services
./docker-manage.sh reset          # Reset with fresh data
./docker-manage.sh status         # Show service status

# Knowledge Graph Operations
./docker-manage.sh init           # Initialize graph constraints
./docker-manage.sh sync           # Sync all data
./docker-manage.sh test           # Test connections
./docker-manage.sh sync-status    # Show sync statistics

# 🤖 GraphRAG API Operations
./docker-manage.sh api-test       # Test GraphRAG API endpoints
./docker-manage.sh query          # Interactive query client
./docker-manage.sh api-logs       # Show GraphRAG API logs
./docker-manage.sh realtime-logs  # Show real-time sync logs

# Development
./docker-manage.sh logs [service] # Show logs
./docker-manage.sh cli            # Access CLI help
./docker-manage.sh browser        # Start with Neo4j browser
```

## 🤖 GraphRAG API Usage

### Natural Language Query Examples

The GraphRAG API translates natural language questions into Cypher queries:

```bash
# Interactive query client
./docker-manage.sh query

# Direct API calls
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Has \"ABC Trading Co\" ever sent \"Automobile parts\" to \"Shanghai Port\"?"}'

# Check API health
curl http://localhost:8000/health

# Get graph statistics
curl http://localhost:8000/stats

# Get example queries
curl http://localhost:8000/query/examples
```

### Supported Question Types

- **Entity Relationships**: "Has X ever sent Y to Z?"
- **Risk Assessment**: "Is ABC Trading high risk?"
- **Product Analysis**: "What products did XYZ Corporation send?"
- **Counting Queries**: "How many documents are in the system?"
- **List Queries**: "List all shippers"
- **Document Search**: "Find documents for ABC Trading"

### API Response Format

```json
{
  "question": "Has \"ABC Trading Co\" ever sent \"Automobile parts\" to \"Shanghai Port\"?",
  "answer": "Yes, the entity has sent the specified items to the destination.",
  "cypher_query": "MATCH (shipper:LegalEntity {name: $shipper})<-[:HAS_SHIPPER]-(d:Document) ...",
  "results": [...],
  "execution_time_ms": 45.2,
  "confidence": 0.95
}
```

## 🔄 Real-time CDC (Change Data Capture)

The system automatically detects and syncs changes when `hitl_finished_at` is updated:

### CDC Triggers

```sql
-- Automatic notification when human-in-the-loop correction is completed
CREATE TRIGGER trigger_hitl_finished
    AFTER UPDATE ON document_fields
    FOR EACH ROW
    EXECUTE FUNCTION notify_hitl_finished();
```

### Real-time Sync Process

1. **PostgreSQL Trigger**: Fires when `hitl_finished_at` is updated
2. **Notification**: Sends JSON payload with document and field details
3. **CDC Listener**: Async service listens for PostgreSQL notifications
4. **Immediate Sync**: Automatically syncs affected document to Neo4j
5. **API Update**: Notifies GraphRAG API of changes

### Monitoring CDC

```bash
# View real-time sync logs
./docker-manage.sh realtime-logs

# Check sync status
./docker-manage.sh sync-status

# Test CDC by updating a document field
psql -h localhost -U postgres -d logistics_kg -c "
UPDATE document_fields 
SET hitl_finished_at = NOW(), hitl_value = 'Updated Value' 
WHERE id = 1;
"
```

## 📊 CLI Commands

Access the Python CLI directly:

```bash
# Inside the container
docker-compose exec kg_sync python cli.py --help

# Available commands
python cli.py init                    # Initialize graph
python cli.py sync --all              # Sync all data
python cli.py sync --document 123     # Sync specific document
python cli.py status                  # Show statistics
python cli.py test-connection         # Test connections
python cli.py clear                   # Clear graph data
```

## 🔍 Query Examples

### Customer Analysis
```cypher
MATCH (c:Customer)-[:PROCESSED]->(d:Document)
RETURN c.name, count(d) as document_count
ORDER BY document_count DESC
```

### Supply Chain Network
```cypher
MATCH (d:Document)-[:HAS_SHIPPER]->(shipper:LegalEntity)
MATCH (d)-[:HAS_CONSIGNEE]->(consignee:LegalEntity)
RETURN shipper.name, consignee.name, count(d) as shipments
```

### Product Classification
```cypher
MATCH (p:Product)-[:CLASSIFIED_AS]->(h:HSCode)
RETURN h.code, count(p) as product_count
ORDER BY product_count DESC
```

### Trade Flow Analysis
```cypher
MATCH (d:Document)-[:ORIGINATED_FROM]->(origin:Location)
MATCH (d)-[:DESTINED_FOR]->(dest:Location)
RETURN origin.name, dest.name, count(d) as volume
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Test all components
python samples/test_suite.py

# Or via Docker
docker-compose exec kg_sync python /app/samples/test_suite.py
```

Run query examples:

```bash
python samples/query_examples.py
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=logistics_kg
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Logging
LOG_LEVEL=INFO
```

### Field Mappings

Customize field-to-graph mappings in `knowledge_graph_sync.py`:

```python
self.field_mappings = {
    'ShipperName': {
        'node_type': 'LegalEntity',
        'relationship': 'HAS_SHIPPER',
        'create_node': self.neo4j_manager.create_or_update_legal_entity,
        'create_relationship': self.neo4j_manager.create_document_entity_relationship
    },
    # Add more mappings...
}
```

## 🔌 Integration

### Adding New Document Types

1. Add field definitions in PostgreSQL:
```sql
INSERT INTO field_definitions (name, description, field_type, target_graph_label)
VALUES ('NewField', 'Description', 'text', 'TargetLabel');
```

2. Update field mappings in `knowledge_graph_sync.py`

3. Add corresponding Neo4j node creation methods

### Custom Queries

Create custom analytics queries in the `samples/query_examples.py` pattern or access directly via Neo4j Browser.

## 🐛 Troubleshooting

### Common Issues

1. **Services not starting**:
   - Check Docker is running: `docker info`
   - Verify ports are not in use
   - Check logs: `./docker-manage.sh logs`

2. **Connection errors**:
   - Wait for services to be healthy: `./docker-manage.sh status`
   - Test connections: `./docker-manage.sh test`

3. **Sync issues**:
   - Initialize graph first: `./docker-manage.sh init`
   - Check PostgreSQL data exists
   - Review sync logs

### Performance Tuning

- **Neo4j Memory**: Adjust in `docker-compose.yml`
- **PostgreSQL Connections**: Pool size in Python code
- **Batch Processing**: Modify sync batch sizes

## 📈 Scaling

### Horizontal Scaling

- **Read Replicas**: Add PostgreSQL read replicas
- **Neo4j Cluster**: Upgrade to Neo4j Enterprise
- **Microservices**: Split sync service by document type

### Performance Optimization

- **Indexing**: Add appropriate database indexes
- **Caching**: Implement Redis for frequent queries
- **Async Processing**: Use background job queues

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

### Development Setup

```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Setup environment
cp backend/.env.example backend/.env

# Run tests
python samples/test_suite.py
```

## 📄 License

[Add your license information]

## 🆘 Support

For issues and questions:

1. Check troubleshooting section
2. Review test suite output
3. Check container logs
4. Create GitHub issue with details

## 🗺️ Roadmap

- [ ] Real-time streaming sync
- [ ] Advanced analytics dashboard
- [ ] Machine learning integration
- [ ] Multi-tenant support
- [ ] API layer for external integration
- [ ] Web-based management interface

---

**Built with ❤️ for the logistics and trade industry**
