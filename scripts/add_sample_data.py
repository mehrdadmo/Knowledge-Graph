#!/usr/bin/env python3

"""
Quick test script to populate Neo4j with sample data
"""
import os
import sys
sys.path.append('/Users/mehrdadmohamadali/Desktop/Knowledge Graph/backend')

from neo4j_manager import Neo4jManager
from config import settings

def add_sample_data():
    """Add sample data to Neo4j"""
    print("🧪 Adding sample data to Neo4j...")
    
    try:
        neo4j = Neo4jManager()
        
        # Add sample customer
        neo4j.execute_query("""
            MERGE (c:LegalEntity {name: $name, type: 'Customer'})
            SET c.created_at = datetime()
            SET c.updated_at = datetime()
        """, {"name": "Global Logistics Inc"})
        
        # Add sample location
        neo4j.execute_query("""
            MERGE (l:Location {name: $name, type: 'Port'})
            SET l.created_at = datetime()
            SET l.updated_at = datetime()
        """, {"name": "Port of Hamburg"})
        
        # Add sample document
        neo4j.execute_query("""
            MERGE (d:Document {id: $id, document_number: $number, document_type: $type})
            SET d.created_at = datetime()
            SET d.updated_at = datetime()
        """, {"id": 1, "number": "BL12345", "type": "Bill of Lading"})
        
        # Add relationships
        neo4j.execute_query("""
            MATCH (c:LegalEntity {name: 'Global Logistics Inc'})
            MATCH (d:Document {document_number: 'BL12345'})
            MATCH (l:Location {name: 'Port of Hamburg'})
            MERGE (c)-[:SHIPPER]->(d)
            MERGE (d)-[:ORIGIN_PORT]->(l)
        """)
        
        print("✅ Sample data added successfully!")
        print("📊 Added: 1 customer, 1 document, 1 location, 2 relationships")
        
        # Get statistics
        stats = neo4j.get_graph_statistics()
        print(f"📈 Graph Statistics: {stats}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    add_sample_data()
