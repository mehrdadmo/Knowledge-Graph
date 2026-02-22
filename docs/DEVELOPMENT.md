# Development Guide

## Local Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Neo4j 5.15+
- Docker & Docker Compose

### Setup Without Docker

1. **Install PostgreSQL**:
```bash
# Create database
createdb logistics_kg

# Load schema
psql logistics_kg < database/schema.sql
psql logistics_kg < database/sample_data.sql
```

2. **Install Neo4j**:
```bash
# Download and start Neo4j
# Set password: neo4j/password
```

3. **Setup Python Environment**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. **Run CLI**:
```bash
python cli.py --help
```

## Code Structure

### Core Components

- **config.py**: Configuration management using Pydantic
- **database_manager.py**: PostgreSQL operations with connection pooling
- **neo4j_manager.py**: Neo4j operations with session management
- **knowledge_graph_sync.py**: Main sync logic and field mappings
- **cli.py**: Command-line interface using Typer

### Design Patterns

- **Context Managers**: For database connections
- **Factory Pattern**: For node creation based on field types
- **Strategy Pattern**: For different sync operations
- **Repository Pattern**: For data access abstraction

## Testing

### Unit Tests
```bash
# Run specific test methods
python -m pytest tests/test_database_manager.py

# Run with coverage
python -m pytest --cov=backend tests/
```

### Integration Tests
```bash
# Full test suite
python samples/test_suite.py
```

### Manual Testing
```bash
# Test individual components
python cli.py test-connection
python cli.py init
python cli.py sync --all
```

## Adding New Features

### New Field Types

1. **Add Field Definition**:
```sql
INSERT INTO field_definitions (name, description, field_type, target_graph_label)
VALUES ('NewField', 'Description', 'text', 'NewNodeType');
```

2. **Update Field Mappings**:
```python
'NewField': {
    'node_type': 'NewNodeType',
    'relationship': 'HAS_NEW_FIELD',
    'create_node': self.neo4j_manager.create_or_update_new_node,
    'create_relationship': self.neo4j_manager.create_document_new_relationship
}
```

3. **Add Neo4j Methods**:
```python
def create_or_update_new_node(self, name: str) -> None:
    query = """
    MERGE (n:NewNodeType {name: $name})
    SET n.updated_at = datetime()
    """
    params = {"name": name}
    self.execute_query(query, params)
```

### New Query Patterns

Add to `samples/query_examples.py`:

```python
def new_analysis_pattern(self):
    query = """
    MATCH (n:NodeType)-[r:RELATIONSHIP]->(m:TargetType)
    RETURN n.name, m.name, count(r) as count
    ORDER BY count DESC
    """
    return self.run_query("New Analysis Pattern", query)
```

## Performance Optimization

### Database Indexing

Add indexes to `schema.sql`:

```sql
-- Performance indexes
CREATE INDEX CONCURRENTLY idx_document_fields_best_value_gin 
ON document_fields USING gin(to_tsvector('english', best_value));

CREATE INDEX CONCURRENTLY idx_documents_created_at 
ON documents(created_at DESC);
```

### Neo4j Optimization

Update `docker-compose.yml`:

```yaml
neo4j:
  environment:
    NEO4J_dbms_memory_heap_initial__size: 1G
    NEO4J_dbms_memory_heap_max__size: 4G
    NEO4J_dbms_memory_pagecache_size: 2G
```

### Batch Processing

Modify sync logic for batch operations:

```python
def sync_documents_batch(self, batch_size: int = 100):
    documents = self.pg_manager.get_documents()
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        self.process_document_batch(batch)
```

## Monitoring

### Health Checks

Add custom health checks:

```python
def health_check(self) -> Dict[str, bool]:
    return {
        "postgres": self.test_postgres_connection(),
        "neo4j": self.test_neo4j_connection(),
        "sync": self.test_sync_operation()
    }
```

### Metrics

Add metrics collection:

```python
def get_sync_metrics(self) -> Dict[str, Any]:
    return {
        "last_sync_time": self.get_last_sync_timestamp(),
        "total_synced": self.get_total_synced_count(),
        "sync_rate": self.calculate_sync_rate(),
        "error_count": self.get_error_count()
    }
```

## Debugging

### Logging Configuration

Enhance logging in `config.py`:

```python
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "kg_sync.log",
            "formatter": "detailed"
        }
    }
}
```

### Debug Mode

Add debug flag to CLI:

```python
@app.command()
def debug_sync(document_id: int):
    """Debug sync for specific document"""
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    
    sync = KnowledgeGraphSync()
    sync.debug_single_document(document_id)
```

## Deployment

### Production Configuration

1. **Environment Variables**:
```bash
POSTGRES_HOST=postgres-prod
POSTGRES_PASSWORD=secure_password
NEO4J_URI=bolt://neo4j-prod:7687
LOG_LEVEL=WARNING
```

2. **Docker Production**:
```yaml
services:
  kg_sync:
    restart: always
    environment:
      - LOG_LEVEL=WARNING
    volumes:
      - production_logs:/app/logs
```

3. **Security**:
- Use secrets management
- Enable SSL/TLS
- Network isolation
- Regular security updates

### CI/CD Pipeline

Example GitHub Actions:

```yaml
name: Test and Deploy
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
      neo4j:
        image: neo4j:5.15-community
        env:
          NEO4J_AUTH: neo4j/test
    
    steps:
    - uses: actions/checkout@v3
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: pip install -r backend/requirements.txt
    
    - name: Run tests
      run: python samples/test_suite.py
```

## API Integration

### REST API Extension

Add FastAPI for external access:

```python
# api.py
from fastapi import FastAPI
from knowledge_graph_sync import KnowledgeGraphSync

app = FastAPI()
sync = KnowledgeGraphSync()

@app.get("/sync/status")
async def get_sync_status():
    return sync.get_sync_status()

@app.post("/sync/document/{document_id}")
async def sync_document(document_id: int):
    sync.sync_single_document(document_id)
    return {"status": "synced"}
```

### GraphQL Integration

Add GraphQL endpoint:

```python
# graphql_schema.py
import strawberry
from neo4j_manager import Neo4jManager

@strawberry.type
class Query:
    @strawberry.field
    def customers(self) -> List[Customer]:
        # GraphQL resolver
        pass
```

## Contributing Guidelines

### Code Style

- Use Black for formatting
- Follow PEP 8
- Type hints required
- Docstrings for all public methods

### Pull Request Process

1. Create feature branch
2. Add tests
3. Update documentation
4. Submit PR with description
5. Code review
6. Merge to main

### Code Review Checklist

- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Performance considered
- [ ] Security implications reviewed
