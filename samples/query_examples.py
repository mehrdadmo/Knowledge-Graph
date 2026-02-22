#!/usr/bin/env python3
"""
Sample queries for the Logistics Knowledge Graph
This script demonstrates various query patterns for extracting insights
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.neo4j_manager import Neo4jManager
from loguru import logger
from typing import List, Dict, Any
import json


class QueryExamples:
    def __init__(self):
        self.neo4j_manager = Neo4jManager()
    
    def run_query(self, description: str, query: str, params: Dict = None) -> List[Dict]:
        """Run a query and display results"""
        logger.info(f"Query: {description}")
        logger.info(f"Cypher: {query}")
        
        try:
            results = self.neo4j_manager.execute_query(query, params)
            logger.info(f"Results: {len(results)} records")
            
            for i, result in enumerate(results[:5]):  # Show first 5 results
                logger.info(f"  {i+1}: {result}")
            
            if len(results) > 5:
                logger.info(f"  ... and {len(results) - 5} more")
            
            return results
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def customer_overview(self):
        """Get overview of customers and their document activity"""
        query = """
        MATCH (c:Customer)-[:PROCESSED]->(d:Document)
        RETURN c.name as customer, 
               c.email as email,
               count(d) as total_documents,
               collect(d.document_type) as document_types
        ORDER BY total_documents DESC
        """
        return self.run_query(
            "Customer Overview - Documents processed by each customer",
            query
        )
    
    def supply_chain_network(self):
        """Get supply chain relationships between entities"""
        query = """
        MATCH (d:Document)-[:HAS_SHIPPER]->(shipper:LegalEntity)
        MATCH (d)-[:HAS_CONSIGNEE]->(consignee:LegalEntity)
        RETURN shipper.name as shipper,
               consignee.name as consignee,
               count(d) as shipments
        ORDER BY shipments DESC
        LIMIT 10
        """
        return self.run_query(
            "Supply Chain Network - Shipper to Consignee relationships",
            query
        )
    
    def product_classification_analysis(self):
        """Analyze product classifications and HS codes"""
        query = """
        MATCH (p:Product)-[:CLASSIFIED_AS]->(h:HSCode)
        RETURN h.code as hs_code,
               count(p) as product_count,
               collect(p.name)[0..3] as sample_products
        ORDER BY product_count DESC
        LIMIT 10
        """
        return self.run_query(
            "Product Classification Analysis - HS codes and their products",
            query
        )
    
    def trade_flow_analysis(self):
        """Analyze trade flows between locations"""
        query = """
        MATCH (d:Document)-[:ORIGINATED_FROM]->(origin:Location)
        MATCH (d)-[:DESTINED_FOR]->(dest:Location)
        RETURN origin.name as origin_port,
               dest.name as destination_port,
               count(d) as shipment_volume
        ORDER BY shipment_volume DESC
        LIMIT 10
        """
        return self.run_query(
            "Trade Flow Analysis - Origin to Destination patterns",
            query
        )
    
    def entity_document_network(self):
        """Find entities mentioned across multiple documents"""
        query = """
        MATCH (e:LegalEntity)<-[:HAS_SHIPPER|:HAS_CONSIGNEE]-(d:Document)
        RETURN e.name as entity,
               count(d) as document_mentions,
               collect(d.document_number)[0..3] as sample_documents
        ORDER BY document_mentions DESC
        LIMIT 10
        """
        return self.run_query(
            "Entity Document Network - Entities across multiple documents",
            query
        )
    
    def document_complexity_analysis(self):
        """Analyze document complexity based on extracted fields"""
        query = """
        MATCH (d:Document)
        OPTIONAL MATCH (d)-[:HAS_SHIPPER]->(s:LegalEntity)
        OPTIONAL MATCH (d)-[:HAS_CONSIGNEE]->(c:LegalEntity)
        OPTIONAL MATCH (d)-[:CONTAINS]->(p:Product)
        OPTIONAL MATCH (d)-[:ORIGINATED_FROM]->(o:Location)
        OPTIONAL MATCH (d)-[:DESTINED_FOR]->(dest:Location)
        RETURN d.document_number,
               d.document_type,
               count(DISTINCT s) + count(DISTINCT c) + count(DISTINCT p) + 
               count(DISTINCT o) + count(DISTINCT dest) as complexity_score
        ORDER BY complexity_score DESC
        LIMIT 10
        """
        return self.run_query(
            "Document Complexity Analysis - Richness of extracted information",
            query
        )
    
    def hs_code_hierarchy_exploration(self):
        """Explore HS code patterns and hierarchies"""
        query = """
        MATCH (p:Product)-[:CLASSIFIED_AS]->(h:HSCode)
        WITH h, count(p) as product_count
        RETURN h.code as hs_code,
               product_count,
               substring(h.code, 0, 4) as chapter,
               substring(h.code, 0, 2) as heading
        ORDER BY heading, chapter, hs_code
        LIMIT 15
        """
        return self.run_query(
            "HS Code Hierarchy Exploration - Chapter and heading patterns",
            query
        )
    
    def customer_entity_relationships(self):
        """Find relationships between customers and legal entities"""
        query = """
        MATCH (c:Customer)-[:PROCESSED]->(d:Document)-[r]->(e:LegalEntity)
        RETURN c.name as customer,
               e.name as entity,
               type(r) as relationship_type,
               count(d) as document_count
        ORDER BY customer, document_count DESC
        LIMIT 15
        """
        return self.run_query(
            "Customer-Entity Relationships - How customers work with entities",
            query
        )
    
    def path_analysis(self):
        """Find paths between entities through documents"""
        query = """
        MATCH path = (shipper:LegalEntity)<-[:HAS_SHIPPER]-(d:Document)-[:HAS_CONSIGNEE]->(consignee:LegalEntity)
        WHERE shipper <> consignee
        RETURN shipper.name as shipper,
               d.document_number as document,
               consignee.name as consignee
        ORDER BY shipper, consignee
        LIMIT 10
        """
        return self.run_query(
            "Path Analysis - Supply chain paths through documents",
            query
        )
    
    def run_all_examples(self):
        """Run all query examples"""
        logger.info("Running Knowledge Graph Query Examples")
        logger.info("=" * 60)
        
        examples = [
            self.customer_overview,
            self.supply_chain_network,
            self.product_classification_analysis,
            self.trade_flow_analysis,
            self.entity_document_network,
            self.document_complexity_analysis,
            self.hs_code_hierarchy_exploration,
            self.customer_entity_relationships,
            self.path_analysis
        ]
        
        for example in examples:
            try:
                example()
                logger.info("-" * 60)
            except Exception as e:
                logger.error(f"Example failed: {e}")
                logger.info("-" * 60)
        
        logger.info("Query examples completed!")


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level="INFO"
    )
    
    # Run examples
    query_examples = QueryExamples()
    query_examples.run_all_examples()
