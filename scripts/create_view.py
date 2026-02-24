#!/usr/bin/env python3
"""
Create the missing database view
"""
import psycopg2
import sys

def get_connection():
    """Get PostgreSQL connection"""
    try:
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

def create_view():
    """Create the missing view"""
    print("🔧 Creating document_fields_view...")
    
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create the view
        view_sql = """
        CREATE OR REPLACE VIEW document_fields_view AS
        SELECT 
            df.id,
            df.document_id,
            d.document_number,
            d.customer_id,
            c.name as customer_name,
            fd.name as field_name,
            fd.target_graph_label,
            CASE 
                WHEN df.hitl_value IS NOT NULL AND df.hitl_value != '' THEN df.hitl_value
                WHEN df.normalized_value IS NOT NULL AND df.normalized_value != '' THEN df.normalized_value
                ELSE df.raw_value
            END as best_value,
            df.raw_value,
            df.normalized_value,
            df.hitl_value,
            df.confidence_score,
            df.created_at
        FROM document_fields df
        JOIN documents d ON df.document_id = d.id
        JOIN customers c ON d.customer_id = c.id
        JOIN field_definitions fd ON df.field_definition_id = fd.id
        """
        
        cursor.execute(view_sql)
        conn.commit()
        
        print("✅ View created successfully!")
        
        # Test the view
        cursor.execute("SELECT COUNT(*) FROM document_fields_view WHERE hitl_finished_at IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"📊 HITL approved fields in view: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = create_view()
    sys.exit(0 if success else 1)
