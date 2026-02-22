#!/usr/bin/env python3
"""
Test script for the Knowledge Graph system
This script tests various components of the knowledge graph pipeline
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database_manager import PostgreSQLManager
from backend.neo4j_manager import Neo4jManager
from backend.knowledge_graph_sync import KnowledgeGraphSync
from loguru import logger
import time


class TestSuite:
    def __init__(self):
        self.pg_manager = PostgreSQLManager()
        self.neo4j_manager = Neo4jManager()
        self.sync = KnowledgeGraphSync()
        
    def test_postgres_connection(self):
        """Test PostgreSQL connection and data"""
        logger.info("Testing PostgreSQL connection...")
        
        try:
            # Test basic connection
            customers = self.pg_manager.get_customers()
            logger.info(f"✅ Connected to PostgreSQL. Found {len(customers)} customers")
            
            # Test document fields
            fields = self.pg_manager.get_document_fields()
            logger.info(f"✅ Found {len(fields)} document fields")
            
            # Test specific queries
            documents = self.pg_manager.get_documents()
            field_defs = self.pg_manager.get_field_definitions()
            
            logger.info(f"✅ Found {len(documents)} documents and {len(field_defs)} field definitions")
            return True
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL test failed: {e}")
            return False
    
    def test_neo4j_connection(self):
        """Test Neo4j connection"""
        logger.info("Testing Neo4j connection...")
        
        try:
            # Test basic connection
            stats = self.neo4j_manager.get_graph_statistics()
            logger.info(f"✅ Connected to Neo4j. Graph statistics: {stats}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Neo4j test failed: {e}")
            return False
    
    def test_graph_initialization(self):
        """Test graph constraint creation"""
        logger.info("Testing graph initialization...")
        
        try:
            self.sync.initialize_graph()
            logger.info("✅ Graph constraints created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Graph initialization failed: {e}")
            return False
    
    def test_data_sync(self):
        """Test full data synchronization"""
        logger.info("Testing data synchronization...")
        
        try:
            # Clear graph first
            self.neo4j_manager.clear_graph()
            
            # Perform sync
            self.sync.sync_all_data()
            
            # Verify results
            stats = self.neo4j_manager.get_graph_statistics()
            total_nodes = sum(stats[k] for k in stats if k != "relationships")
            
            if total_nodes > 0:
                logger.info(f"✅ Data sync successful. Created {total_nodes} nodes")
                return True
            else:
                logger.error("❌ No nodes created during sync")
                return False
                
        except Exception as e:
            logger.error(f"❌ Data sync test failed: {e}")
            return False
    
    def test_single_document_sync(self):
        """Test single document synchronization"""
        logger.info("Testing single document sync...")
        
        try:
            # Get first document
            documents = self.pg_manager.get_documents()
            if not documents:
                logger.warning("⚠️ No documents found to test single sync")
                return True
            
            doc_id = documents[0]['id']
            
            # Clear and sync single document
            self.neo4j_manager.clear_graph()
            self.sync.sync_single_document(doc_id)
            
            # Verify
            stats = self.neo4j_manager.get_graph_statistics()
            total_nodes = sum(stats[k] for k in stats if k != "relationships")
            
            logger.info(f"✅ Single document sync successful. Created {total_nodes} nodes")
            return True
            
        except Exception as e:
            logger.error(f"❌ Single document sync test failed: {e}")
            return False
    
    def test_query_patterns(self):
        """Test common graph query patterns"""
        logger.info("Testing graph query patterns...")
        
        try:
            # Test customer-document relationships
            query = """
            MATCH (c:Customer)-[:PROCESSED]->(d:Document)
            RETURN c.name as customer, count(d) as document_count
            ORDER BY document_count DESC
            """
            results = self.neo4j_manager.execute_query(query)
            logger.info(f"✅ Customer query successful: {len(results)} results")
            
            # Test product-HS code relationships
            query = """
            MATCH (p:Product)-[:CLASSIFIED_AS]->(h:HSCode)
            RETURN p.name as product, h.code as hs_code
            LIMIT 5
            """
            results = self.neo4j_manager.execute_query(query)
            logger.info(f"✅ Product-HS code query successful: {len(results)} results")
            
            # Test document-entity relationships
            query = """
            MATCH (d:Document)-[:HAS_SHIPPER]->(e:LegalEntity)
            RETURN d.document_number, e.name as shipper
            LIMIT 5
            """
            results = self.neo4j_manager.execute_query(query)
            logger.info(f"✅ Document-shipper query successful: {len(results)} results")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Query pattern test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests and return results"""
        logger.info("Starting comprehensive test suite...")
        
        tests = [
            ("PostgreSQL Connection", self.test_postgres_connection),
            ("Neo4j Connection", self.test_neo4j_connection),
            ("Graph Initialization", self.test_graph_initialization),
            ("Data Synchronization", self.test_data_sync),
            ("Single Document Sync", self.test_single_document_sync),
            ("Query Patterns", self.test_query_patterns)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                result = test_func()
                results[test_name] = result
                status = "PASS" if result else "FAIL"
                logger.info(f"Test result: {status}")
                
            except Exception as e:
                logger.error(f"Test crashed: {e}")
                results[test_name] = False
            
            # Small delay between tests
            time.sleep(1)
        
        # Summary
        logger.info(f"\n{'='*50}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*50}")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        return passed == total


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level="INFO"
    )
    
    # Run tests
    test_suite = TestSuite()
    success = test_suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
