import re
import json
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger
from schemas import EntityExtraction


class NLToCypherTranslator:
    """
    Translates natural language questions into Cypher queries
    for the logistics knowledge graph
    """
    
    def __init__(self):
        # Entity patterns and their corresponding graph labels
        self.entity_patterns = {
            'shipper': 'LegalEntity',
            'consignee': 'LegalEntity', 
            'customer': 'Customer',
            'product': 'Product',
            'hs_code': 'HSCode',
            'location': 'Location',
            'port': 'Location',
            'document': 'Document'
        }
        
        # Relationship patterns
        self.relationship_patterns = {
            'sent': 'HAS_SHIPPER',
            'received': 'HAS_CONSIGNEE',
            'processed': 'PROCESSED',
            'contains': 'CONTAINS',
            'classified_as': 'CLASSIFIED_AS',
            'originated_from': 'ORIGINATED_FROM',
            'destined_for': 'DESTINED_FOR',
            'shipped_to': 'DESTINED_FOR',
            'shipped_from': 'ORIGINATED_FROM'
        }
        
        # Question type patterns
        self.question_patterns = {
            'has_ever': self._handle_has_ever_question,
            'is_high_risk': self._handle_risk_question,
            'how_many': self._handle_how_many_question,
            'what_products': self._handle_what_products_question,
            'which_customers': self._handle_which_customers_question,
            'list_all': self._handle_list_all_question,
            'find_documents': self._handle_find_documents_question
        }
    
    def translate(self, question: str) -> Tuple[str, Dict[str, Any]]:
        """
        Translate natural language question to Cypher query
        
        Args:
            question: Natural language question
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        question_lower = question.lower().strip()
        
        # Extract entities and constraints
        entities = self._extract_entities(question)
        
        # Determine question type and generate query
        for pattern, handler in self.question_patterns.items():
            if pattern in question_lower:
                return handler(question, entities)
        
        # Default fallback
        return self._handle_generic_question(question, entities)
    
    def _extract_entities(self, question: str) -> EntityExtraction:
        """Extract entities, relationships, and constraints from question"""
        entities = []
        relationships = []
        constraints = []
        
        # Extract quoted entities (exact matches)
        quoted_entities = re.findall(r'"([^"]+)"', question)
        entities.extend(quoted_entities)
        
        # Extract entity types
        for entity_type in self.entity_patterns.keys():
            if entity_type in question.lower():
                entities.append(entity_type)
        
        # Extract relationship indicators
        for rel_type in self.relationship_patterns.keys():
            if rel_type in question.lower():
                relationships.append(rel_type)
        
        # Extract specific names (proper nouns - simplified)
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', question)
        constraints.extend(words)
        
        return EntityExtraction(
            entities=list(set(entities)),
            relationships=list(set(relationships)),
            constraints=list(set(constraints))
        )
    
    def _handle_has_ever_question(self, question: str, entities: EntityExtraction) -> Tuple[str, Dict[str, Any]]:
        """Handle 'Has X ever sent Y to Z?' type questions"""
        # Extract specific entities
        shipper = self._extract_quoted_value(question, 'shipper') or self._find_entity_by_type(question, 'shipper')
        product = self._extract_quoted_value(question, 'product') or self._find_entity_by_type(question, 'product')
        destination = self._extract_quoted_value(question, 'destination') or self._find_entity_by_type(question, 'port')
        
        if shipper and product and destination:
            query = """
            MATCH (shipper:LegalEntity {name: $shipper})<-[:HAS_SHIPPER]-(d:Document)
            MATCH (d)-[:CONTAINS]->(product:Product {name: $product})
            MATCH (d)-[:DESTINED_FOR]->(dest:Location {name: $destination})
            RETURN count(d) > 0 as has_ever_sent
            """
            params = {"shipper": shipper, "product": product, "destination": destination}
            return query, params
        
        # Fallback with partial matches
        if shipper and destination:
            query = """
            MATCH (shipper:LegalEntity {name: $shipper})<-[:HAS_SHIPPER]-(d:Document)
            MATCH (d)-[:DESTINED_FOR]->(dest:Location {name: $destination})
            RETURN count(d) > 0 as has_ever_sent
            """
            params = {"shipper": shipper, "destination": destination}
            return query, params
        
        return self._handle_generic_question(question, entities)
    
    def _handle_risk_question(self, question: str, entities: EntityExtraction) -> Tuple[str, Dict[str, Any]]:
        """Handle 'Is X high risk?' type questions"""
        entity = self._extract_quoted_value(question) or self._find_entity_by_type(question, 'shipper')
        
        if entity:
            # Risk assessment based on document patterns and destinations
            query = """
            MATCH (entity:LegalEntity {name: $entity})<-[:HAS_SHIPPER]-(d:Document)
            OPTIONAL MATCH (d)-[:DESTINED_FOR]->(dest:Location)
            WITH entity, count(d) as total_shipments, collect(DISTINCT dest.name) as destinations
            RETURN 
                entity.name as entity,
                total_shipments,
                size(destinations) as unique_destinations,
                CASE 
                    WHEN total_shipments > 100 THEN 'High'
                    WHEN total_shipments > 50 THEN 'Medium'
                    ELSE 'Low'
                END as risk_level,
                CASE 
                    WHEN total_shipments > 100 THEN true
                    ELSE false
                END as is_high_risk
            """
            params = {"entity": entity}
            return query, params
        
        return self._handle_generic_question(question, entities)
    
    def _handle_how_many_question(self, question: str, entities: EntityExtraction) -> Tuple[str, Dict[str, Any]]:
        """Handle 'How many X?' type questions"""
        if 'document' in entities.entities:
            query = "MATCH (d:Document) RETURN count(d) as total_documents"
            return query, {}
        
        if 'shipper' in entities.entities or 'consignee' in entities.entities:
            query = "MATCH (e:LegalEntity) RETURN count(e) as total_entities"
            return query, {}
        
        if 'product' in entities.entities:
            query = "MATCH (p:Product) RETURN count(p) as total_products"
            return query, {}
        
        return self._handle_generic_question(question, entities)
    
    def _handle_what_products_question(self, question: str, entities: EntityExtraction) -> Tuple[str, Dict[str, Any]]:
        """Handle 'What products did X send?' type questions"""
        entity = self._extract_quoted_value(question) or self._find_entity_by_type(question, 'shipper')
        
        if entity:
            query = """
            MATCH (entity:LegalEntity {name: $entity})<-[:HAS_SHIPPER]-(d:Document)
            MATCH (d)-[:CONTAINS]->(p:Product)
            RETURN DISTINCT p.name as product, count(d) as shipment_count
            ORDER BY shipment_count DESC
            LIMIT 20
            """
            params = {"entity": entity}
            return query, params
        
        return self._handle_generic_question(question, entities)
    
    def _handle_which_customers_question(self, question: str, entities: EntityExtraction) -> Tuple[str, Dict[str, Any]]:
        """Handle 'Which customers process X?' type questions"""
        query = """
        MATCH (c:Customer)-[:PROCESSED]->(d:Document)
        RETURN c.name as customer, count(d) as document_count
        ORDER BY document_count DESC
        """
        return query, {}
    
    def _handle_list_all_question(self, question: str, entities: EntityExtraction) -> Tuple[str, Dict[str, Any]]:
        """Handle 'List all X' type questions"""
        if 'shipper' in entities.entities or 'consignee' in entities.entities:
            query = """
            MATCH (e:LegalEntity)
            OPTIONAL MATCH (e)<-[:HAS_SHIPPER|:HAS_CONSIGNEE]-(d:Document)
            RETURN e.name as entity, count(d) as document_count
            ORDER BY document_count DESC
            LIMIT 50
            """
            return query, {}
        
        if 'product' in entities.entities:
            query = """
            MATCH (p:Product)
            OPTIONAL MATCH (p)<-[:CONTAINS]-(d:Document)
            RETURN p.name as product, count(d) as document_count
            ORDER BY document_count DESC
            LIMIT 50
            """
            return query, {}
        
        return self._handle_generic_question(question, entities)
    
    def _handle_find_documents_question(self, question: str, entities: EntityExtraction) -> Tuple[str, Dict[str, Any]]:
        """Handle 'Find documents for X' type questions"""
        entity = self._extract_quoted_value(question)
        
        if entity:
            query = """
            MATCH (d:Document)
            WHERE d.document_number CONTAINS $entity
               OR EXISTS {
                   MATCH (d)-[:HAS_SHIPPER|:HAS_CONSIGNEE]-(e:LegalEntity)
                   WHERE e.name CONTAINS $entity
               }
            RETURN DISTINCT d.document_number, d.document_type, d.created_at
            ORDER BY d.created_at DESC
            LIMIT 20
            """
            params = {"entity": entity}
            return query, params
        
        return self._handle_generic_question(question, entities)
    
    def _handle_generic_question(self, question: str, entities: EntityExtraction) -> Tuple[str, Dict[str, Any]]:
        """Generic fallback for unrecognized question patterns"""
        # Try to find any entities mentioned
        entity = self._extract_quoted_value(question) or (entities.constraints[0] if entities.constraints else None)
        
        if entity:
            query = """
            MATCH (n)
            WHERE n.name CONTAINS $entity
            RETURN labels(n) as types, n.name as name, properties(n) as properties
            LIMIT 10
            """
            params = {"entity": entity}
            return query, params
        
        # Return basic graph overview
        query = """
        MATCH (n)
        WITH labels(n) as types, count(n) as count
        RETURN types[0] as node_type, count
        ORDER BY count DESC
        """
        return query, {}
    
    def _extract_quoted_value(self, question: str, entity_type: str = None) -> Optional[str]:
        """Extract quoted values from question"""
        quoted_values = re.findall(r'"([^"]+)"', question)
        if quoted_values:
            return quoted_values[0]
        return None
    
    def _find_entity_by_type(self, question: str, entity_type: str) -> Optional[str]:
        """Find entity value by type in question"""
        patterns = [
            rf'{entity_type}[:\s]+([A-Z][A-Za-z\s]+?)(?:\s+to|\s+and|\?|$)',
            rf'{entity_type}\s+([A-Z][A-Za-z\s]+?)(?:\s+to|\s+and|\?|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def format_answer(self, question: str, results: List[Dict[str, Any]], cypher_query: str) -> str:
        """Format query results into natural language answer"""
        if not results:
            return f"No results found for your question: '{question}'"
        
        # Handle boolean questions
        if len(results) == 1 and 'has_ever_sent' in results[0]:
            answer = "Yes" if results[0]['has_ever_sent'] else "No"
            return f"{answer}, the entity has {'sent' if results[0]['has_ever_sent'] else 'not sent'} the specified items to the destination."
        
        # Handle risk questions
        if len(results) == 1 and 'is_high_risk' in results[0]:
            risk_level = results[0].get('risk_level', 'Unknown')
            is_high_risk = results[0].get('is_high_risk', False)
            answer = "Yes" if is_high_risk else "No"
            return f"{answer}, this entity has a {risk_level.lower()} risk level based on {results[0].get('total_shipments', 0)} total shipments."
        
        # Handle count questions
        if len(results) == 1 and any(key in results[0] for key in ['total_documents', 'total_entities', 'total_products']):
            count = list(results[0].values())[0]
            return f"There are {count} items matching your question."
        
        # Handle list questions
        if len(results) > 1:
            items = [str(list(r.values())[0]) for r in results[:10]]
            if len(items) < len(results):
                items.append(f"... and {len(results) - 10} more")
            return f"Found {len(results)} items: {', '.join(items)}"
        
        # Default: return first result
        return f"Result: {results[0]}"
