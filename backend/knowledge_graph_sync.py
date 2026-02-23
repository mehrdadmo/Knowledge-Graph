from typing import Dict, Any, List
from loguru import logger
from database_manager import PostgreSQLManager
from neo4j_manager import Neo4jManager


class KnowledgeGraphSync:
    def __init__(self):
        self.pg_manager = PostgreSQLManager()
        self.neo4j_manager = Neo4jManager()
        
        # Mapping of field names to graph operations
        self.field_mappings = {
            'ShipperName': {
                'node_type': 'LegalEntity',
                'relationship': 'HAS_SHIPPER',
                'create_node': self.neo4j_manager.create_or_update_legal_entity,
                'create_relationship': self.neo4j_manager.create_document_entity_relationship
            },
            'ConsigneeName': {
                'node_type': 'LegalEntity',
                'relationship': 'HAS_CONSIGNEE',
                'create_node': self.neo4j_manager.create_or_update_legal_entity,
                'create_relationship': self.neo4j_manager.create_document_entity_relationship
            },
            'HS_Code': {
                'node_type': 'HSCode',
                'relationship': None,
                'create_node': self.neo4j_manager.create_or_update_hs_code,
                'create_relationship': None
            },
            'Product': {
                'node_type': 'Product',
                'relationship': 'CONTAINS',
                'create_node': self.neo4j_manager.create_or_update_product,
                'create_relationship': self.neo4j_manager.create_document_contains_relationship
            },
            'OriginPort': {
                'node_type': 'Location',
                'relationship': 'ORIGINATED_FROM',
                'create_node': self.neo4j_manager.create_or_update_location,
                'create_relationship': self.neo4j_manager.create_document_location_relationship
            },
            'DestinationPort': {
                'node_type': 'Location',
                'relationship': 'DESTINED_FOR',
                'create_node': self.neo4j_manager.create_or_update_location,
                'create_relationship': self.neo4j_manager.create_document_location_relationship
            }
        }
    
    def initialize_graph(self) -> None:
        """Initialize the graph with constraints"""
        logger.info("Initializing Neo4j graph with constraints...")
        self.neo4j_manager.create_constraints()
        logger.info("Graph initialization completed")
    
    def sync_all_data(self) -> None:
        """Sync all data from PostgreSQL to Neo4j"""
        logger.info("Starting full data synchronization...")
        
        # Clear existing graph
        self.neo4j_manager.clear_graph()
        
        # Sync customers
        self.sync_customers()
        
        # Sync documents and their fields
        self.sync_documents()
        
        logger.info("Data synchronization completed")
    
    def sync_customers(self) -> None:
        """Sync customers from PostgreSQL to Neo4j"""
        logger.info("Syncing customers...")
        customers = self.pg_manager.get_customers()
        
        for customer in customers:
            self.neo4j_manager.create_or_update_customer(
                customer_id=customer['id'],
                name=customer['name'],
                email=customer.get('email')
            )
        
        logger.info(f"Synced {len(customers)} customers")
    
    def sync_documents(self) -> None:
        """Sync documents and their fields from PostgreSQL to Neo4j"""
        logger.info("Syncing documents and fields...")
        
        # Get all documents
        documents = self.pg_manager.get_documents()
        
        # Group document fields by document
        document_fields = self.pg_manager.get_document_fields()
        fields_by_document = {}
        
        for field in document_fields:
            doc_id = field['document_id']
            if doc_id not in fields_by_document:
                fields_by_document[doc_id] = []
            fields_by_document[doc_id].append(field)
        
        # Process each document
        for document in documents:
            doc_id = document['id']
            
            # Create document node
            self.neo4j_manager.create_or_update_document(
                document_id=doc_id,
                document_number=document['document_number'] or f"DOC-{doc_id}",
                document_type=document['document_type'],
                customer_id=document['customer_id']
            )
            
            # Create customer-document relationship
            self.neo4j_manager.create_customer_document_relationship(
                customer_id=document['customer_id'],
                document_id=doc_id
            )
            
            # Process document fields
            if doc_id in fields_by_document:
                self.sync_document_fields(doc_id, fields_by_document[doc_id])
        
        logger.info(f"Synced {len(documents)} documents")
    
    def sync_document_fields(self, document_id: int, fields: List[Dict[str, Any]]) -> None:
        """Sync fields for a specific document"""
        product_hs_codes = {}  # Track product-HS code relationships
        
        for field in fields:
            field_name = field['field_name']
            best_value = field['best_value']
            
            if not best_value or field_name not in self.field_mappings:
                continue
            
            mapping = self.field_mappings[field_name]
            
            # Create the node
            mapping['create_node'](best_value)
            
            # Create relationship if applicable
            if mapping['create_relationship']:
                if field_name == 'Product':
                    # For products, we need to handle the relationship differently
                    # to track product-HS code relationships
                    product_hs_codes[best_value] = None
                elif field_name in ['OriginPort', 'DestinationPort']:
                    # Location relationships
                    mapping['create_relationship'](
                        document_id=document_id,
                        location_name=best_value,
                        relationship_type=mapping['relationship']
                    )
                else:
                    # Entity relationships (ShipperName, ConsigneeName, etc.)
                    mapping['create_relationship'](
                        document_id=document_id,
                        entity_name=best_value,
                        relationship_type=mapping['relationship']
                    )
            elif field_name == 'HS_Code':
                # Store HS code to potentially link with products
                # Find if there's a product in the same document
                for other_field in fields:
                    if other_field['field_name'] == 'Product':
                        product_hs_codes[other_field['best_value']] = best_value
                        break
        
        # Create product-HS code relationships and document-product relationships
        for product_name, hs_code in product_hs_codes.items():
            # Create document-product relationship
            self.neo4j_manager.create_document_contains_relationship(
                document_id=document_id,
                product_name=product_name
            )
            
            # Create product-HS code relationship if HS code exists
            if hs_code:
                self.neo4j_manager.create_product_hs_code_relationship(
                    product_name=product_name,
                    hs_code=hs_code
                )
    
    def sync_single_document(self, document_id: int) -> None:
        """Sync a single document from PostgreSQL to Neo4j"""
        logger.info(f"Syncing single document: {document_id}")
        
        # Get document details
        documents = self.pg_manager.get_documents()
        document = next((d for d in documents if d['id'] == document_id), None)
        
        if not document:
            logger.error(f"Document {document_id} not found")
            return
        
        # Create/update document node
        self.neo4j_manager.create_or_update_document(
            document_id=document_id,
            document_number=document['document_number'] or f"DOC-{document_id}",
            document_type=document['document_type'],
            customer_id=document['customer_id']
        )
        
        # Create customer-document relationship
        self.neo4j_manager.create_customer_document_relationship(
            customer_id=document['customer_id'],
            document_id=document_id
        )
        
        # Sync document fields
        fields = self.pg_manager.get_document_fields(document_id)
        if fields:
            self.sync_document_fields(document_id, fields)
        
        logger.info(f"Synced document {document_id}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get the current sync status"""
        # Get PostgreSQL stats
        pg_stats = {
            "customers": len(self.pg_manager.get_customers()),
            "documents": len(self.pg_manager.get_documents()),
            "document_fields": len(self.pg_manager.get_document_fields())
        }
        
        # Get Neo4j stats
        neo4j_stats = self.neo4j_manager.get_graph_statistics()
        
        return {
            "postgresql": pg_stats,
            "neo4j": neo4j_stats,
            "last_sync": "Not available"  # TODO: Implement sync timestamp tracking
        }
