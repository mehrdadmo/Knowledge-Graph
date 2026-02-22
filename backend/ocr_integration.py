#!/usr/bin/env python3
"""
OCR to Knowledge Graph Integration
Bridge between OCR system and Knowledge Graph with real-time CDC
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add paths for both systems
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'OCR', 'backend'))

from config import settings as kg_settings
from neo4j_manager import Neo4jManager
from psycopg2.extras import RealDictCursor
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRToKGIntegration:
    """
    Integration bridge between OCR system and Knowledge Graph
    Handles the complete pipeline: OCR → PostgreSQL → Neo4j → GraphRAG
    """
    
    def __init__(self):
        self.neo4j_manager = Neo4jManager()
        self.ocr_db_config = {
            'host': os.getenv('OCR_DB_HOST', 'localhost'),
            'port': os.getenv('OCR_DB_PORT', '5432'),
            'database': os.getenv('OCR_DB_NAME', 'ocr_db'),
            'user': os.getenv('OCR_DB_USER', 'postgres'),
            'password': os.getenv('OCR_DB_PASSWORD', 'password')
        }
        self.kg_db_config = {
            'host': kg_settings.postgres_host,
            'port': kg_settings.postgres_port,
            'database': kg_settings.postgres_database,
            'user': kg_settings.postgres_user,
            'password': kg_settings.postgres_password
        }
        
        # Field mapping from OCR to KG schema
        self.field_mapping = {
            # OCR field → KG field definition
            'SHIPPER / CONSIGNOR': {
                'kg_field': 'ShipperName',
                'entity_type': 'LegalEntity',
                'relationship': 'HAS_SHIPPER'
            },
            'CONSIGNEE': {
                'kg_field': 'ConsigneeName', 
                'entity_type': 'LegalEntity',
                'relationship': 'HAS_CONSIGNEE'
            },
            'NOTIFY PARTY': {
                'kg_field': 'NotifyPartyName',
                'entity_type': 'LegalEntity', 
                'relationship': 'HAS_NOTIFY_PARTY'
            },
            'DESCRIPTION OF GOODS AS PER P/L': {
                'kg_field': 'ProductDescription',
                'entity_type': 'Product',
                'relationship': 'CONTAINS'
            },
            'PORT OF LOADING': {
                'kg_field': 'OriginPort',
                'entity_type': 'Location',
                'relationship': 'ORIGINATED_FROM'
            },
            'PORT OF DISCHARGE': {
                'kg_field': 'DestinationPort',
                'entity_type': 'Location', 
                'relationship': 'DESTINED_FOR'
            },
            'ORIGIN': {
                'kg_field': 'CountryOfOrigin',
                'entity_type': 'Location',
                'relationship': 'ORIGINATED_FROM'
            },
            'IRANIAN CUSTOMS TARIFF NO': {
                'kg_field': 'HSCode',
                'entity_type': 'HSCode',
                'relationship': 'CLASSIFIED_AS'
            }
        }
    
    def get_ocr_connection(self):
        """Get connection to OCR database"""
        return psycopg2.connect(**self.ocr_db_config)
    
    def get_kg_connection(self):
        """Get connection to Knowledge Graph database"""
        return psycopg2.connect(**self.kg_db_config)
    
    async def sync_document_to_kg(self, document_id: int) -> bool:
        """
        Sync a single document from OCR system to Knowledge Graph
        """
        try:
            logger.info(f"Starting sync for OCR document {document_id}")
            
            # 1️⃣ Get document from OCR database
            ocr_document = await self.get_ocr_document(document_id)
            if not ocr_document:
                logger.error(f"Document {document_id} not found in OCR database")
                return False
            
            # 2️⃣ Create document in KG database
            kg_document_id = await self.create_kg_document(ocr_document)
            
            # 3️⃣ Extract and map fields
            document_fields = await self.extract_document_fields(document_id)
            
            # 4️⃣ Create entities and relationships in Neo4j
            await self.sync_to_neo4j(kg_document_id, document_fields, ocr_document)
            
            # 5️⃣ Trigger CDC for real-time updates
            await self.trigger_cdc_notifications(kg_document_id, document_fields)
            
            logger.info(f"Successfully synced document {document_id} to KG")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync document {document_id}: {str(e)}")
            return False
    
    async def get_ocr_document(self, document_id: int) -> Optional[Dict]:
        """Get document from OCR database"""
        try:
            conn = self.get_ocr_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
            SELECT d.*, b.user_id as batch_user_id
            FROM core_document d
            LEFT JOIN core_batch b ON d.batch_id = b.id
            WHERE d.id = %s
            """
            
            cursor.execute(query, (document_id,))
            result = cursor.fetchone()
            
            conn.close()
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Error getting OCR document {document_id}: {str(e)}")
            return None
    
    async def create_kg_document(self, ocr_document: Dict) -> int:
        """Create document in KG database"""
        try:
            conn = self.get_kg_connection()
            cursor = conn.cursor()
            
            # Create customer if not exists
            customer_id = await self.get_or_create_customer(ocr_document.get('batch_user_id'))
            
            # Create document
            query = """
            INSERT INTO documents (customer_id, document_number, document_type, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """
            
            document_number = f"OCR-{ocr_document['id']}"
            document_type = self.detect_document_type(ocr_document)
            created_at = ocr_document.get('uploaded_at', datetime.now())
            
            cursor.execute(query, (customer_id, document_number, document_type, created_at))
            kg_document_id = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created KG document {kg_document_id} for OCR document {ocr_document['id']}")
            return kg_document_id
            
        except Exception as e:
            logger.error(f"Error creating KG document: {str(e)}")
            raise
    
    async def get_or_create_customer(self, user_id: Optional[int]) -> int:
        """Get or create customer in KG database"""
        try:
            conn = self.get_kg_connection()
            cursor = conn.cursor()
            
            # Try to find existing customer
            query = "SELECT id FROM customers WHERE ocr_user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Create new customer
            query = """
            INSERT INTO customers (name, ocr_user_id)
            VALUES (%s, %s)
            RETURNING id
            """
            customer_name = f"OCR User {user_id}" if user_id else "OCR System"
            cursor.execute(query, (customer_name, user_id))
            customer_id = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            return customer_id
            
        except Exception as e:
            logger.error(f"Error getting/creating customer: {str(e)}")
            raise
    
    async def extract_document_fields(self, document_id: int) -> List[Dict]:
        """Extract fields from OCR document"""
        try:
            conn = self.get_ocr_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
            SELECT df.normalized_value, df.hitl_value, f.group, f.name
            FROM core_documentfield df
            JOIN core_field f ON df.field_id = f.id
            WHERE df.document_id = %s
            """
            
            cursor.execute(query, (document_id,))
            results = cursor.fetchall()
            
            conn.close()
            
            # Convert to list of dicts
            fields = []
            for result in results:
                field_dict = dict(result)
                # Prefer HITL value over normalized value
                field_dict['final_value'] = field_dict['hitl_value'] or field_dict['normalized_value']
                fields.append(field_dict)
            
            return fields
            
        except Exception as e:
            logger.error(f"Error extracting fields for document {document_id}: {str(e)}")
            return []
    
    async def sync_to_neo4j(self, kg_document_id: int, document_fields: List[Dict], ocr_document: Dict):
        """Sync entities and relationships to Neo4j"""
        try:
            # Create document node
            await self.create_document_node(kg_document_id, ocr_document)
            
            # Process each field
            for field in document_fields:
                field_name = field['name']
                field_value = field['final_value']
                
                if not field_value or field_name not in self.field_mapping:
                    continue
                
                mapping = self.field_mapping[field_name]
                
                # Create entity node
                entity_id = await self.create_entity_node(
                    mapping['entity_type'],
                    field_value,
                    field
                )
                
                # Create relationship
                await self.create_relationship(
                    kg_document_id,
                    entity_id,
                    mapping['relationship'],
                    field
                )
            
            logger.info(f"Synced {len(document_fields)} fields to Neo4j for document {kg_document_id}")
            
        except Exception as e:
            logger.error(f"Error syncing to Neo4j: {str(e)}")
            raise
    
    async def create_document_node(self, document_id: int, ocr_document: Dict):
        """Create document node in Neo4j"""
        query = """
        MERGE (d:Document {id: $document_id})
        SET d.document_number = $document_number,
            d.document_type = $document_type,
            d.ocr_id = $ocr_id,
            ocr_confidence = $ocr_confidence,
            d.created_at = datetime(),
            d.source = 'ocr_integration'
        """
        
        params = {
            'document_id': document_id,
            'document_number': f"OCR-{ocr_document['id']}",
            'document_type': self.detect_document_type(ocr_document),
            'ocr_id': ocr_document['id'],
            'ocr_confidence': ocr_document.get('ocr_confidence', 0.0)
        }
        
        await self.neo4j_manager.execute_query(query, params)
    
    async def create_entity_node(self, entity_type: str, entity_name: str, field: Dict) -> int:
        """Create entity node in Neo4j"""
        query = f"""
        MERGE (e:{entity_type} {{name: $entity_name}})
        SET e.source = 'ocr_integration',
            e.extracted_from = $field_name,
            e.confidence = $confidence,
            e.created_at = datetime()
        RETURN e.id as entity_id
        """
        
        params = {
            'entity_name': entity_name,
            'field_name': field['name'],
            'confidence': 0.8 if field['hitl_value'] else 0.6
        }
        
        result = await self.neo4j_manager.execute_query(query, params)
        return result[0]['entity_id'] if result else None
    
    async def create_relationship(self, document_id: int, entity_id: int, relationship_type: str, field: Dict):
        """Create relationship between document and entity"""
        query = f"""
        MATCH (d:Document {{id: $document_id}})
        MATCH (e) WHERE id(e) = $entity_id
        MERGE (d)-[:{relationship_type}]->(e)
        SET r.extracted_from = $field_name,
            r.confidence = $confidence,
            r.created_at = datetime()
        """
        
        params = {
            'document_id': document_id,
            'entity_id': entity_id,
            'field_name': field['name'],
            'confidence': 0.8 if field['hitl_value'] else 0.6
        }
        
        await self.neo4j_manager.execute_query(query, params)
    
    async def trigger_cdc_notifications(self, kg_document_id: int, document_fields: List[Dict]):
        """Trigger CDC notifications for real-time updates"""
        try:
            # This would normally be handled by PostgreSQL triggers
            # For now, we'll simulate the CDC notification
            for field in document_fields:
                if field['hitl_value']:  # Only trigger for HITL-corrected fields
                    await self.send_cdc_notification(kg_document_id, field)
        
        except Exception as e:
            logger.error(f"Error triggering CDC: {str(e)}")
    
    async def send_cdc_notification(self, document_id: int, field: Dict):
        """Send CDC notification (simulated)"""
        notification = {
            'channel': 'hitl_finished',
            'payload': {
                'document_id': document_id,
                'field_name': field['name'],
                'field_value': field['hitl_value'],
                'timestamp': datetime.now().isoformat()
            }
        }
        
        logger.info(f"CDC Notification: {notification}")
        # In real implementation, this would trigger PostgreSQL NOTIFY
    
    def detect_document_type(self, ocr_document: Dict) -> str:
        """Detect document type from OCR data"""
        normalized_json = ocr_document.get('normalized_json', {})
        
        if isinstance(normalized_json, dict):
            # Check for key indicators
            if 'B/L NO. & DATE' in normalized_json:
                return 'bill_of_lading'
            elif 'REFERENCE NO.' in normalized_json and 'DATE OF ISSUE' in normalized_json:
                return 'inspection_certificate'
            elif any(key in normalized_json for key in ['P/I NO.DATE', 'C/I NO.DATE']):
                return 'invoice'
        
        return 'unknown'
    
    async def batch_sync_recent_documents(self, limit: int = 10) -> Dict:
        """Sync recent documents from OCR to KG"""
        try:
            conn = self.get_ocr_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get recent documents with HITL corrections
            query = """
            SELECT d.id, d.hitl_finished_at
            FROM core_document d
            WHERE d.hitl_finished_at IS NOT NULL
            ORDER BY d.hitl_finished_at DESC
            LIMIT %s
            """
            
            cursor.execute(query, (limit,))
            documents = cursor.fetchall()
            conn.close()
            
            results = {
                'total': len(documents),
                'synced': 0,
                'failed': 0,
                'details': []
            }
            
            for doc in documents:
                success = await self.sync_document_to_kg(doc['id'])
                if success:
                    results['synced'] += 1
                    results['details'].append({
                        'document_id': doc['id'],
                        'status': 'success',
                        'hitl_finished_at': doc['hitl_finished_at']
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'document_id': doc['id'],
                        'status': 'failed',
                        'hitl_finished_at': doc['hitl_finished_at']
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch sync: {str(e)}")
            return {'error': str(e)}
    
    async def get_sync_status(self) -> Dict:
        """Get sync status between OCR and KG"""
        try:
            # Get OCR document count
            ocr_conn = self.get_ocr_connection()
            ocr_cursor = ocr_conn.cursor()
            ocr_cursor.execute("SELECT COUNT(*) FROM core_document WHERE hitl_finished_at IS NOT NULL")
            ocr_count = ocr_cursor.fetchone()[0]
            ocr_conn.close()
            
            # Get KG document count from OCR source
            kg_conn = self.get_kg_connection()
            kg_cursor = kg_conn.cursor()
            kg_cursor.execute("SELECT COUNT(*) FROM documents WHERE document_number LIKE 'OCR-%'")
            kg_count = kg_cursor.fetchone()[0]
            kg_conn.close()
            
            # Get Neo4j statistics
            neo4j_stats = self.neo4j_manager.get_graph_statistics()
            
            return {
                'ocr_documents_with_hitl': ocr_count,
                'kg_documents_from_ocr': kg_count,
                'sync_percentage': (kg_count / ocr_count * 100) if ocr_count > 0 else 0,
                'neo4j_stats': neo4j_stats,
                'last_sync': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting sync status: {str(e)}")
            return {'error': str(e)}

# CLI interface
async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OCR to Knowledge Graph Integration')
    parser.add_argument('--sync-document', type=int, help='Sync specific document ID')
    parser.add_argument('--batch-sync', type=int, help='Batch sync recent documents (limit)')
    parser.add_argument('--status', action='store_true', help='Get sync status')
    parser.add_argument('--test', action='store_true', help='Test integration')
    
    args = parser.parse_args()
    
    integration = OCRToKGIntegration()
    
    if args.sync_document:
        success = await integration.sync_document_to_kg(args.sync_document)
        print(f"Sync result: {'SUCCESS' if success else 'FAILED'}")
    
    elif args.batch_sync:
        result = await integration.batch_sync_recent_documents(args.batch_sync)
        print(f"Batch sync result: {json.dumps(result, indent=2)}")
    
    elif args.status:
        status = await integration.get_sync_status()
        print(f"Sync status: {json.dumps(status, indent=2)}")
    
    elif args.test:
        print("Testing OCR to KG integration...")
        # Test with a sample document
        status = await integration.get_sync_status()
        print(f"Test completed. Status: {json.dumps(status, indent=2)}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
