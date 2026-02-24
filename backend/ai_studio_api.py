#!/usr/bin/env python3
"""
AI Studio Integration for Knowledge Graph Platform
Provides endpoints optimized for Google AI Studio
"""

import os
import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from datetime import datetime

# Knowledge Graph imports
from neo4j_manager import Neo4jManager
from nl_to_cypher import NLToCypherTranslator
from compliance_engine import ComplianceEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Knowledge Graph AI Studio API",
    description="AI Studio optimized endpoints for Knowledge Graph Platform",
    version="1.0.0"
)

# CORS for AI Studio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # AI Studio domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
neo4j_manager = Neo4jManager()
nl_translator = NLToCypherTranslator()
compliance_engine = ComplianceEngine()

# Pydantic models for AI Studio
class AIQueryRequest(BaseModel):
    query: str
    context: Optional[str] = None
    max_results: Optional[int] = 10
    include_compliance: Optional[bool] = False

class AIQueryResponse(BaseModel):
    query: str
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    cypher_query: Optional[str] = None
    compliance_status: Optional[Dict[str, Any]] = None
    processing_time: float
    timestamp: datetime

class EntityExtractionRequest(BaseModel):
    text: str
    entity_types: Optional[List[str]] = ["LegalEntity", "Product", "Location"]

class EntityExtractionResponse(BaseModel):
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]

class ComplianceCheckRequest(BaseModel):
    document_text: str
    document_type: Optional[str] = "trade_document"
    compliance_rules: Optional[List[str]] = None

class ComplianceCheckResponse(BaseModel):
    overall_status: str
    risk_score: float
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    processing_time: float

@app.get("/")
async def root():
    """Health check for AI Studio"""
    return {
        "service": "Knowledge Graph AI Studio API",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "capabilities": [
            "natural_language_queries",
            "entity_extraction",
            "compliance_checking",
            "relationship_analysis"
        ]
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test Neo4j connection
        graph_stats = neo4j_manager.get_graph_statistics()
        
        # Test compliance engine
        compliance_rules = len(compliance_engine.rules)
        
        return {
            "status": "healthy",
            "neo4j_connected": True,
            "graph_stats": graph_stats,
            "compliance_rules": compliance_rules,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/ai/query", response_model=AIQueryResponse)
async def ai_query(request: AIQueryRequest, background_tasks: BackgroundTasks):
    """AI Studio optimized query endpoint"""
    start_time = datetime.now()
    
    try:
        logger.info(f"AI Query: {request.query}")
        
        # 1. Translate natural language to Cypher
        cypher_query, params = nl_translator.translate(request.query)
        
        # 2. Execute graph query
        results = await neo4j_manager.execute_query(cypher_query, params)
        
        # 3. Generate natural language answer
        answer = generate_ai_answer(request.query, results)
        
        # 4. Extract sources
        sources = extract_sources(results)
        
        # 5. Calculate confidence
        confidence = calculate_confidence(results, request.query)
        
        # 6. Optional compliance check
        compliance_status = None
        if request.include_compliance:
            compliance_status = await get_compliance_context(results)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Log the query for analytics (fire and forget)
        background_tasks.add_task(log_ai_query, request.query, answer, confidence)
        
        return AIQueryResponse(
            query=request.query,
            answer=answer,
            confidence=confidence,
            sources=sources,
            cypher_query=cypher_query,
            compliance_status=compliance_status,
            processing_time=processing_time,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"AI Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.post("/ai/extract-entities", response_model=EntityExtractionResponse)
async def extract_entities(request: EntityExtractionRequest):
    """Extract entities from text using graph intelligence"""
    try:
        logger.info(f"Extracting entities from text: {request.text[:100]}...")
        
        # 1. Extract potential entities
        entities = extract_entities_from_text(request.text)
        
        # 2. Match entities against graph
        matched_entities = await match_entities_in_graph(entities, request.entity_types)
        
        # 3. Find relationships between entities
        relationships = await find_entity_relationships(matched_entities)
        
        # 4. Calculate confidence scores
        confidence_scores = calculate_entity_confidence(matched_entities, relationships)
        
        return EntityExtractionResponse(
            entities=matched_entities,
            relationships=relationships,
            confidence_scores=confidence_scores
        )
        
    except Exception as e:
        logger.error(f"Entity extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")

@app.post("/ai/compliance-check", response_model=ComplianceCheckResponse)
async def ai_compliance_check(request: ComplianceCheckRequest):
    """AI-powered compliance checking"""
    start_time = datetime.now()
    
    try:
        logger.info(f"AI Compliance check for {request.document_type}")
        
        # 1. Extract entities from document
        entities = extract_entities_from_text(request.document_text)
        
        # 2. Create document structure for compliance engine
        document_data = create_document_structure(entities, request.document_type)
        
        # 3. Run compliance checks
        if request.compliance_rules:
            # Run specific rules
            results = await run_specific_compliance_rules(request.compliance_rules, document_data)
        else:
            # Run all compliance rules
            report = await compliance_engine.check_document_compliance(999999)  # Use test ID
        
        # 4. Calculate risk score
        risk_score = calculate_risk_score(results if request.compliance_rules else report.results)
        
        # 5. Generate recommendations
        recommendations = generate_compliance_recommendations(results if request.compliance_rules else report.results)
        
        # 6. Format violations
        violations = format_compliance_violations(results if request.compliance_rules else report.results)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ComplianceCheckResponse(
            overall_status=report.overall_status.value if not request.compliance_rules else "COMPLIANT",
            risk_score=risk_score,
            violations=violations,
            recommendations=recommendations,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"AI Compliance check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {str(e)}")

@app.get("/ai/graph-stats")
async def get_graph_statistics():
    """Get graph statistics for AI Studio"""
    try:
        stats = neo4j_manager.get_graph_statistics()
        
        # Calculate additional AI-relevant metrics
        total_entities = sum([
            stats.get('customers', 0),
            stats.get('products', 0),
            stats.get('locations', 0),
            stats.get('legal_entities', 0)
        ])
        
        total_relationships = sum(stats.get('relationships', {}).values())
        
        return {
            "total_documents": stats.get('documents', 0),
            "total_entities": total_entities,
            "total_relationships": total_relationships,
            "entity_breakdown": {
                "customers": stats.get('customers', 0),
                "products": stats.get('products', 0),
                "locations": stats.get('locations', 0),
                "legal_entities": stats.get('legal_entities', 0),
                "hs_codes": stats.get('hs_codes', 0)
            },
            "relationship_breakdown": stats.get('relationships', {}),
            "ai_ready": True,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Graph stats failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get graph statistics: {str(e)}")

# Helper functions for AI Studio integration
def generate_ai_answer(query: str, results: List[Dict]) -> str:
    """Generate natural language answer from query results"""
    if not results:
        return "I couldn't find any information matching your query."
    
    # Simple answer generation - can be enhanced with LLM
    if len(results) == 1:
        return f"Based on the knowledge graph, {results[0].get('answer', 'information was found')}"
    else:
        return f"Found {len(results)} results matching your query. The most relevant information shows {results[0].get('answer', 'various entities and relationships')}"

def extract_sources(results: List[Dict]) -> List[Dict[str, Any]]:
    """Extract source information from results"""
    sources = []
    for result in results[:5]:  # Limit to top 5 sources
        sources.append({
            "type": "graph_node",
            "id": result.get("id", "unknown"),
            "label": result.get("name", result.get("label", "Unknown")),
            "properties": {k: v for k, v in result.items() if k not in ["id", "name", "label"]}
        })
    return sources

def calculate_confidence(results: List[Dict], query: str) -> float:
    """Calculate confidence score for the answer"""
    if not results:
        return 0.0
    
    # Simple confidence calculation based on result quality
    base_confidence = 0.7
    result_quality = min(len(results) / 10, 0.3)  # More results = higher confidence
    
    return min(base_confidence + result_quality, 1.0)

async def get_compliance_context(results: List[Dict]) -> Dict[str, Any]:
    """Get compliance context for query results"""
    # This would check if any entities in results have compliance issues
    return {
        "status": "compliant",
        "risk_level": "low",
        "last_check": datetime.now().isoformat()
    }

def extract_entities_from_text(text: str) -> List[str]:
    """Extract potential entities from text"""
    # Simple entity extraction - can be enhanced with NLP
    import re
    
    # Extract potential company names (uppercase words)
    companies = re.findall(r'\b[A-Z]{2,}\s+(?:CORP|LTD|INC|LLC|GMBH|CO)\b', text)
    
    # Extract potential locations
    locations = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    
    # Extract potential product descriptions
    products = re.findall(r'\b(?:machine|equipment|product|goods|material|item)\b[^.]*', text, re.IGNORECASE)
    
    return list(set(companies + locations + products))

async def match_entities_in_graph(entities: List[str], entity_types: List[str]) -> List[Dict[str, Any]]:
    """Match extracted entities against graph"""
    matched_entities = []
    
    for entity in entities:
        for entity_type in entity_types:
            query = f"""
            MATCH (e:{entity_type})
            WHERE e.name CONTAINS $entity_name
            RETURN e.name as name, labels(e) as types, properties(e) as properties
            LIMIT 5
            """
            
            results = await neo4j_manager.execute_query(query, {"entity_name": entity})
            
            for result in results:
                matched_entities.append({
                    "name": result["name"],
                    "type": entity_type,
                    "properties": result["properties"],
                    "match_score": calculate_match_score(entity, result["name"])
                })
    
    return matched_entities

def calculate_match_score(extracted: str, graph_name: str) -> float:
    """Calculate match score between extracted entity and graph entity"""
    # Simple string similarity - can be enhanced
    extracted_lower = extracted.lower()
    graph_name_lower = graph_name.lower()
    
    if extracted_lower == graph_name_lower:
        return 1.0
    elif extracted_lower in graph_name_lower or graph_name_lower in extracted_lower:
        return 0.8
    else:
        # Simple word overlap
        extracted_words = set(extracted_lower.split())
        graph_words = set(graph_name_lower.split())
        overlap = extracted_words & graph_words
        
        if overlap:
            return len(overlap) / max(len(extracted_words), len(graph_words))
        else:
            return 0.0

async def find_entity_relationships(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find relationships between matched entities"""
    relationships = []
    
    for i, entity1 in enumerate(entities):
        for entity2 in entities[i+1:]:
            query = """
            MATCH (e1)-[r]->(e2)
            WHERE e1.name = $name1 AND e2.name = $name2
            RETURN type(r) as relationship_type, properties(r) as rel_properties
            """
            
            results = await neo4j_manager.execute_query(query, {
                "name1": entity1["name"],
                "name2": entity2["name"]
            })
            
            for result in results:
                relationships.append({
                    "from": entity1["name"],
                    "to": entity2["name"],
                    "type": result["relationship_type"],
                    "properties": result["rel_properties"]
                })
    
    return relationships

def calculate_entity_confidence(entities: List[Dict], relationships: List[Dict]) -> Dict[str, float]:
    """Calculate confidence scores for entities"""
    confidence_scores = {}
    
    for entity in entities:
        base_score = entity["match_score"]
        
        # Boost confidence if entity has relationships
        entity_relationships = [r for r in relationships 
                               if r["from"] == entity["name"] or r["to"] == entity["name"]]
        
        if entity_relationships:
            relationship_boost = min(len(entity_relationships) * 0.1, 0.3)
            final_score = min(base_score + relationship_boost, 1.0)
        else:
            final_score = base_score
        
        confidence_scores[entity["name"]] = final_score
    
    return confidence_scores

def create_document_structure(entities: List[str], document_type: str) -> Dict[str, Any]:
    """Create document structure for compliance engine"""
    return {
        "document_id": 999999,
        "document_number": f"AI-CHECK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "entities": [
            {
                "name": entity,
                "type": "LegalEntity",
                "properties": {},
                "relationship": "MENTIONED_IN"
            }
            for entity in entities
        ]
    }

async def run_specific_compliance_rules(rules: List[str], document_data: Dict) -> List[Dict]:
    """Run specific compliance rules"""
    results = []
    
    for rule_id in rules:
        rule = next((r for r in compliance_engine.rules if r.id == rule_id), None)
        if rule:
            result = await compliance_engine.check_rule(rule, document_data)
            results.append({
                "rule_id": result.rule_id,
                "status": result.status.value,
                "severity": result.severity.value,
                "message": result.message
            })
    
    return results

def calculate_risk_score(results: List[Dict]) -> float:
    """Calculate overall risk score"""
    if not results:
        return 0.0
    
    severity_weights = {
        "CRITICAL": 1.0,
        "HIGH": 0.8,
        "MEDIUM": 0.6,
        "LOW": 0.4,
        "INFO": 0.2
    }
    
    total_weight = 0
    total_score = 0
    
    for result in results:
        if result["status"] != "COMPLIANT":
            weight = severity_weights.get(result["severity"], 0.5)
            total_weight += weight
            total_score += weight
    
    return total_score / len(results) if results else 0.0

def generate_compliance_recommendations(results: List[Dict]) -> List[str]:
    """Generate compliance recommendations"""
    recommendations = []
    
    for result in results:
        if result["status"] != "COMPLIANT":
            if "IBAN" in result["rule_id"]:
                recommendations.append("Validate IBAN format and country sanctions")
            elif "SANCTION" in result["rule_id"]:
                recommendations.append("Review entity against sanctions lists")
            elif "HS_CODE" in result["rule_id"]:
                recommendations.append("Check HS code trade restrictions")
            else:
                recommendations.append(f"Address {result['rule_id']} compliance issue")
    
    return recommendations

def format_compliance_violations(results: List[Dict]) -> List[Dict[str, Any]]:
    """Format compliance violations"""
    violations = []
    
    for result in results:
        if result["status"] != "COMPLIANT":
            violations.append({
                "rule": result["rule_id"],
                "severity": result["severity"],
                "message": result["message"],
                "timestamp": datetime.now().isoformat()
            })
    
    return violations

async def log_ai_query(query: str, answer: str, confidence: float):
    """Log AI query for analytics"""
    # This would log to a database or analytics service
    logger.info(f"AI Query logged: {query[:50]}... (confidence: {confidence})")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
