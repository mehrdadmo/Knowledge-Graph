import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from loguru import logger
from config import settings


class PostgreSQLManager:
    def __init__(self):
        self.dsn = settings.postgres_dsn
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            # Check if using Cloud SQL Unix socket
            if settings.postgres_host.startswith("/cloudsql/"):
                # For Cloud SQL Unix socket, we need to connect differently
                conn = psycopg2.connect(
                    host=settings.postgres_host,
                    port=settings.postgres_port,
                    database=settings.postgres_db,
                    user=settings.postgres_user,
                    password=settings.postgres_password
                )
            else:
                # Regular TCP connection
                conn = psycopg2.connect(self.dsn)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    if cursor.description:
                        results = [dict(row) for row in cursor.fetchall()]
                        return results
                    return []
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an update/insert/delete query and return affected row count"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"Update execution error: {e}")
            raise
    
    def get_document_fields(self, document_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get document fields with best values, optionally filtered by document_id"""
        query = """
        SELECT * FROM document_fields_view
        """
        params = None
        
        if document_id:
            query += " WHERE document_id = %s"
            params = (document_id,)
        
        query += " ORDER BY document_id, field_name"
        
        return self.execute_query(query, params)
    
    def get_customers(self) -> List[Dict[str, Any]]:
        """Get all customers"""
        query = "SELECT * FROM customers ORDER BY name"
        return self.execute_query(query)
    
    def get_documents(self, customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get documents, optionally filtered by customer_id"""
        query = """
        SELECT d.*, c.name as customer_name 
        FROM documents d 
        JOIN customers c ON d.customer_id = c.id
        """
        params = None
        
        if customer_id:
            query += " WHERE d.customer_id = %s"
            params = (customer_id,)
        
        query += " ORDER BY d.created_at DESC"
        
        return self.execute_query(query, params)
    
    def get_field_definitions(self) -> List[Dict[str, Any]]:
        """Get all field definitions"""
        query = "SELECT * FROM field_definitions ORDER BY name"
        return self.execute_query(query)
