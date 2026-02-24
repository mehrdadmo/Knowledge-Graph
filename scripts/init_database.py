#!/usr/bin/env python3
"""
Initialize database schema for Knowledge Graph
"""
import psycopg2
import os
from psycopg2.extras import RealDictCursor
import sys

def get_connection():
    """Get PostgreSQL connection"""
    try:
        # Use the same connection as the Cloud Run service
        conn = psycopg2.connect(
            host="35.222.9.67",
            port=5432,
            database="logistics_kg",
            user="postgres",
            password="KnowledgeGraph2024!"
        )
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def initialize_database():
    """Initialize the database schema"""
    print("🔧 Initializing database schema...")
    
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create tables
        create_statements = [
            """
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                document_type VARCHAR(100) NOT NULL,
                document_number VARCHAR(255),
                file_path VARCHAR(500),
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS field_definitions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                field_type VARCHAR(50) NOT NULL,
                target_graph_label VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS document_fields (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL REFERENCES documents(id),
                field_definition_id INTEGER NOT NULL REFERENCES field_definitions(id),
                raw_value TEXT,
                normalized_value TEXT,
                hitl_value TEXT,
                confidence_score DECIMAL(3,2),
                hitl_finished_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(document_id, field_definition_id)
            )
            """
        ]
        
        print("📋 Creating tables...")
        for statement in create_statements:
            cursor.execute(statement)
        
        # Insert field definitions
        field_defs = [
            ('ShipperName', 'Name of the shipper', 'text', 'LegalEntity'),
            ('ConsigneeName', 'Name of the consignee', 'text', 'LegalEntity'),
            ('OriginPort', 'Origin port', 'text', 'Location'),
            ('DestinationPort', 'Destination port', 'text', 'Location'),
            ('HS_Code', 'HS Code', 'text', 'HSCode'),
            ('Product', 'Product description', 'text', 'Product'),
            ('Price', 'Price', 'number', 'Product'),
            ('Quantity', 'Quantity', 'number', 'Product')
        ]
        
        print("📝 Inserting field definitions...")
        for name, desc, ftype, label in field_defs:
            cursor.execute(
                "INSERT INTO field_definitions (name, description, field_type, target_graph_label) VALUES (%s, %s, %s, %s) ON CONFLICT (name) DO NOTHING",
                (name, desc, ftype, label)
            )
        
        # Insert sample customer and documents (simulating your HITL data)
        print("👤 Creating sample customer...")
        cursor.execute(
            "INSERT INTO customers (name, email) VALUES (%s, %s) ON CONFLICT (email) DO NOTHING",
            ('Global Logistics Inc', 'info@globallogistics.com')
        )
        
        # Get customer ID
        cursor.execute("SELECT id FROM customers WHERE name = 'Global Logistics Inc'")
        customer_id = cursor.fetchone()[0]
        
        print("📄 Creating sample documents...")
        sample_docs = [
            (customer_id, 'Bill of Lading', 'BL2024001'),
            (customer_id, 'Invoice', 'INV2024001'),
            (customer_id, 'Bill of Lading', 'BL2024002'),
            (customer_id, 'Invoice', 'INV2024002')
        ]
        
        for cust_id, doc_type, doc_num in sample_docs:
            cursor.execute(
                "INSERT INTO documents (customer_id, document_type, document_number) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (cust_id, doc_type, doc_num)
            )
        
        # Get document IDs and add sample fields (simulating HITL approved data)
        cursor.execute("SELECT id, document_number FROM documents ORDER BY id")
        documents = cursor.fetchall()
        
        print("🏷️ Adding sample document fields (HITL approved)...")
        sample_fields = [
            # Document 1 - BL2024001
            (1, 'ShipperName', 'ABC Trading Company', None, 'ABC Trading Company', 0.95, '2026-02-24 16:00:00'),
            (1, 'ConsigneeName', 'XYZ Corporation', None, 'XYZ Corporation', 0.92, '2026-02-24 16:00:00'),
            (1, 'OriginPort', 'Port of Hamburg', None, 'Port of Hamburg', 0.98, '2026-02-24 16:00:00'),
            (1, 'DestinationPort', 'Port of Shanghai', None, 'Port of Shanghai', 0.97, '2026-02-24 16:00:00'),
            (1, 'Product', 'Electronics', None, 'Consumer Electronics', 0.89, '2026-02-24 16:00:00'),
            (1, 'HS_Code', '8517', None, '8517', 0.94, '2026-02-24 16:00:00'),
            
            # Document 2 - INV2024001
            (2, 'ShipperName', 'ABC Trading Company', None, 'ABC Trading Company', 0.96, '2026-02-24 16:05:00'),
            (2, 'ConsigneeName', 'XYZ Corporation', None, 'XYZ Corporation', 0.93, '2026-02-24 16:05:00'),
            (2, 'Product', 'Electronics', None, 'Smartphones', 0.91, '2026-02-24 16:05:00'),
            (2, 'Price', '15000', None, '15000.00', 0.88, '2026-02-24 16:05:00'),
            (2, 'Quantity', '100', None, '100', 0.95, '2026-02-24 16:05:00'),
            
            # Document 3 - BL2024002
            (3, 'ShipperName', 'Global Export Ltd', None, 'Global Export Ltd', 0.94, '2026-02-24 16:10:00'),
            (3, 'ConsigneeName', 'Import Solutions Inc', None, 'Import Solutions Inc', 0.92, '2026-02-24 16:10:00'),
            (3, 'OriginPort', 'Port of Rotterdam', None, 'Port of Rotterdam', 0.97, '2026-02-24 16:10:00'),
            (3, 'DestinationPort', 'Port of New York', None, 'Port of New York', 0.96, '2026-02-24 16:10:00'),
            (3, 'Product', 'Machinery', None, 'Industrial Machinery', 0.90, '2026-02-24 16:10:00'),
            
            # Document 4 - INV2024002
            (4, 'ShipperName', 'Global Export Ltd', None, 'Global Export Ltd', 0.95, '2026-02-24 16:15:00'),
            (4, 'ConsigneeName', 'Import Solutions Inc', None, 'Import Solutions Inc', 0.93, '2026-02-24 16:15:00'),
            (4, 'Product', 'Machinery', None, 'CNC Machines', 0.91, '2026-02-24 16:15:00'),
            (4, 'Price', '75000', None, '75000.00', 0.89, '2026-02-24 16:15:00'),
            (4, 'Quantity', '5', None, '5', 0.94, '2026-02-24 16:15:00'),
        ]
        
        for doc_id, field_name, raw_val, norm_val, hitl_val, confidence, hitl_time in sample_fields:
            # Get field definition ID
            cursor.execute("SELECT id FROM field_definitions WHERE name = %s", (field_name,))
            field_def_id = cursor.fetchone()[0]
            
            cursor.execute(
                """INSERT INTO document_fields 
                   (document_id, field_definition_id, raw_value, normalized_value, hitl_value, confidence_score, hitl_finished_at) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (document_id, field_definition_id) DO UPDATE SET
                   hitl_value = EXCLUDED.hitl_value,
                   hitl_finished_at = EXCLUDED.hitl_finished_at,
                   confidence_score = EXCLUDED.confidence_score""",
                (doc_id, field_def_id, raw_val, norm_val, hitl_val, confidence, hitl_time)
            )
        
        conn.commit()
        
        # Show results
        print("\n✅ Database initialized successfully!")
        print("\n📊 Summary:")
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        print(f"   Customers: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        print(f"   Documents: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM document_fields WHERE hitl_finished_at IS NOT NULL")
        print(f"   HITL Approved Fields: {cursor.fetchone()[0]}")
        
        print("\n🎯 Ready for sync to Neo4j!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = initialize_database()
    sys.exit(0 if success else 1)
