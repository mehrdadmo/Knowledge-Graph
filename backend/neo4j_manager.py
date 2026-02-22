from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from loguru import logger
from config import settings


class Neo4jManager:
    def __init__(self):
        self.uri = settings.neo4j_uri
        self.user = settings.neo4j_user
        self.password = settings.neo4j_password
    
    @contextmanager
    def get_session(self):
        """Context manager for Neo4j sessions"""
        driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        try:
            session = driver.session()
            yield session
        except Exception as e:
            logger.error(f"Neo4j session error: {e}")
            raise
        finally:
            session.close()
            driver.close()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results"""
        try:
            with self.get_session() as session:
                result = session.run(query, params or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Neo4j query error: {e}")
            raise
    
    def clear_graph(self) -> None:
        """Clear all nodes and relationships from the graph"""
        query = "MATCH (n) DETACH DELETE n"
        self.execute_query(query)
        logger.info("Graph cleared successfully")
    
    def create_constraints(self) -> None:
        """Create uniqueness constraints for the graph"""
        constraints = [
            "CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT legal_entity_name_unique IF NOT EXISTS FOR (e:LegalEntity) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT hs_code_code_unique IF NOT EXISTS FOR (h:HSCode) REQUIRE h.code IS UNIQUE",
            "CREATE CONSTRAINT product_name_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT location_name_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                self.execute_query(constraint)
                logger.info(f"Created constraint: {constraint}")
            except Exception as e:
                logger.warning(f"Constraint may already exist: {e}")
    
    def create_or_update_customer(self, customer_id: int, name: str, email: Optional[str] = None) -> None:
        """Create or update a Customer node"""
        query = """
        MERGE (c:Customer {id: $customer_id})
        SET c.name = $name, c.email = $email, c.updated_at = datetime()
        """
        params = {
            "customer_id": customer_id,
            "name": name,
            "email": email
        }
        self.execute_query(query, params)
    
    def create_or_update_document(self, document_id: int, document_number: str, 
                                 document_type: str, customer_id: int) -> None:
        """Create or update a Document node"""
        query = """
        MERGE (d:Document {id: $document_id})
        SET d.document_number = $document_number, 
            d.document_type = $document_type,
            d.customer_id = $customer_id,
            d.updated_at = datetime()
        """
        params = {
            "document_id": document_id,
            "document_number": document_number,
            "document_type": document_type,
            "customer_id": customer_id
        }
        self.execute_query(query, params)
    
    def create_or_update_legal_entity(self, name: str) -> None:
        """Create or update a LegalEntity node"""
        query = """
        MERGE (e:LegalEntity {name: $name})
        SET e.updated_at = datetime()
        """
        params = {"name": name}
        self.execute_query(query, params)
    
    def create_or_update_hs_code(self, code: str) -> None:
        """Create or update an HSCode node"""
        query = """
        MERGE (h:HSCode {code: $code})
        SET h.updated_at = datetime()
        """
        params = {"code": code}
        self.execute_query(query, params)
    
    def create_or_update_product(self, name: str) -> None:
        """Create or update a Product node"""
        query = """
        MERGE (p:Product {name: $name})
        SET p.updated_at = datetime()
        """
        params = {"name": name}
        self.execute_query(query, params)
    
    def create_or_update_location(self, name: str) -> None:
        """Create or update a Location node"""
        query = """
        MERGE (l:Location {name: $name})
        SET l.updated_at = datetime()
        """
        params = {"name": name}
        self.execute_query(query, params)
    
    def create_customer_document_relationship(self, customer_id: int, document_id: int) -> None:
        """Create PROCESSED relationship between Customer and Document"""
        query = """
        MATCH (c:Customer {id: $customer_id})
        MATCH (d:Document {id: $document_id})
        MERGE (c)-[:PROCESSED]->(d)
        """
        params = {"customer_id": customer_id, "document_id": document_id}
        self.execute_query(query, params)
    
    def create_document_entity_relationship(self, document_id: int, entity_name: str, 
                                          relationship_type: str) -> None:
        """Create relationship between Document and LegalEntity"""
        query = f"""
        MATCH (d:Document {{id: $document_id}})
        MATCH (e:LegalEntity {{name: $entity_name}})
        MERGE (d)-[:{relationship_type}]->(e)
        """
        params = {"document_id": document_id, "entity_name": entity_name}
        self.execute_query(query, params)
    
    def create_product_hs_code_relationship(self, product_name: str, hs_code: str) -> None:
        """Create CLASSIFIED_AS relationship between Product and HSCode"""
        query = """
        MATCH (p:Product {name: $product_name})
        MATCH (h:HSCode {code: $hs_code})
        MERGE (p)-[:CLASSIFIED_AS]->(h)
        """
        params = {"product_name": product_name, "hs_code": hs_code}
        self.execute_query(query, params)
    
    def create_document_contains_relationship(self, document_id: int, product_name: str) -> None:
        """Create CONTAINS relationship between Document and Product"""
        query = """
        MATCH (d:Document {id: $document_id})
        MATCH (p:Product {name: $product_name})
        MERGE (d)-[:CONTAINS]->(p)
        """
        params = {"document_id": document_id, "product_name": product_name}
        self.execute_query(query, params)
    
    def create_document_location_relationship(self, document_id: int, location_name: str, 
                                            relationship_type: str) -> None:
        """Create relationship between Document and Location"""
        query = f"""
        MATCH (d:Document {{id: $document_id}})
        MATCH (l:Location {{name: $location_name}})
        MERGE (d)-[:{relationship_type}]->(l)
        """
        params = {"document_id": document_id, "location_name": location_name}
        self.execute_query(query, params)
    
    def get_graph_statistics(self) -> Dict[str, int]:
        """Get statistics about the graph"""
        stats = {}
        
        node_queries = {
            "customers": "MATCH (c:Customer) RETURN count(c) as count",
            "documents": "MATCH (d:Document) RETURN count(d) as count",
            "legal_entities": "MATCH (e:LegalEntity) RETURN count(e) as count",
            "hs_codes": "MATCH (h:HSCode) RETURN count(h) as count",
            "products": "MATCH (p:Product) RETURN count(p) as count",
            "locations": "MATCH (l:Location) RETURN count(l) as count"
        }
        
        for key, query in node_queries.items():
            result = self.execute_query(query)
            stats[key] = result[0]["count"] if result else 0
        
        # Get relationship counts
        rel_query = """
        MATCH ()-[r]->() 
        RETURN type(r) as relationship_type, count(r) as count 
        ORDER BY count DESC
        """
        rel_results = self.execute_query(rel_query)
        stats["relationships"] = {r["relationship_type"]: r["count"] for r in rel_results}
        
        return stats
