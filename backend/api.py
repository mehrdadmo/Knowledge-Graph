from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import asyncio
from typing import Dict, Any, List
from loguru import logger
import json

from schemas import QueryRequest, QueryResponse, CDCNotification, SyncStatus
from neo4j_manager import Neo4jManager
from nl_to_cypher import NLToCypherTranslator
from knowledge_graph_sync import KnowledgeGraphSync
from config import settings

app = FastAPI(
    title="Logistics Knowledge Graph API",
    description="GraphRAG API for logistics and trade knowledge graph",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
neo4j_manager = Neo4jManager()
translator = NLToCypherTranslator()
sync = KnowledgeGraphSync()

# Background task tracking
active_syncs: Dict[str, Dict[str, Any]] = {}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Logistics Knowledge Graph API",
        "version": "1.0.0",
        "endpoints": {
            "query": "/query",
            "health": "/health",
            "stats": "/stats",
            "sync": "/sync"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Neo4j connection
        stats = neo4j_manager.get_graph_statistics()
        return {
            "status": "healthy",
            "neo4j_connected": True,
            "total_nodes": sum(stats[k] for k in stats if k != "relationships")
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_graph(request: QueryRequest):
    """
    GraphRAG endpoint for natural language queries
    
    Examples:
    - "Has this shipper ever sent this product to Poti?"
    - "Is ABC Trading high risk?"
    - "What products did XYZ Corporation send?"
    - "How many documents are in the system?"
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing query: {request.question}")
        
        # Translate natural language to Cypher
        cypher_query, params = translator.translate(request.question)
        logger.info(f"Generated Cypher: {cypher_query}")
        logger.info(f"Parameters: {params}")
        
        # Execute query
        results = neo4j_manager.execute_query(cypher_query, params)
        execution_time = (time.time() - start_time) * 1000
        
        # Format answer
        answer = translator.format_answer(request.question, results, cypher_query)
        
        # Calculate confidence based on result completeness
        confidence = 1.0 if results else 0.5
        if "count" in cypher_query.lower() and results:
            confidence = 0.9
        
        response = QueryResponse(
            question=request.question,
            answer=answer,
            cypher_query=cypher_query,
            results=results,
            execution_time_ms=round(execution_time, 2),
            confidence=confidence
        )
        
        logger.info(f"Query completed in {execution_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        execution_time = (time.time() - start_time) * 1000
        
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


@app.get("/stats")
async def get_graph_statistics():
    """Get current graph statistics"""
    try:
        stats = neo4j_manager.get_graph_statistics()
        return {
            "status": "success",
            "statistics": stats,
            "summary": {
                "total_nodes": sum(stats[k] for k in stats if k != "relationships"),
                "total_relationships": sum(stats.get("relationships", {}).values())
            }
        }
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")


@app.post("/sync/document/{document_id}")
async def sync_document(document_id: int, background_tasks: BackgroundTasks):
    """Trigger sync for specific document"""
    try:
        # Add to background tasks
        task_id = f"sync_doc_{document_id}_{int(time.time())}"
        active_syncs[task_id] = {"status": "pending", "document_id": document_id}
        
        background_tasks.add_task(
            _sync_document_background,
            task_id,
            document_id
        )
        
        return {
            "message": f"Sync started for document {document_id}",
            "task_id": task_id,
            "status": "pending"
        }
    except Exception as e:
        logger.error(f"Sync trigger failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync trigger failed: {str(e)}")


@app.post("/sync/all")
async def sync_all_documents(background_tasks: BackgroundTasks):
    """Trigger full sync of all documents"""
    try:
        task_id = f"sync_all_{int(time.time())}"
        active_syncs[task_id] = {"status": "pending", "type": "full_sync"}
        
        background_tasks.add_task(_sync_all_background, task_id)
        
        return {
            "message": "Full sync started",
            "task_id": task_id,
            "status": "pending"
        }
    except Exception as e:
        logger.error(f"Full sync trigger failed: {e}")
        raise HTTPException(status_code=500, detail=f"Full sync trigger failed: {str(e)}")


@app.get("/sync/status/{task_id}")
async def get_sync_status(task_id: str):
    """Get status of a sync task"""
    if task_id not in active_syncs:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return active_syncs[task_id]


@app.post("/cdc/notification")
async def handle_cdc_notification(notification: CDCNotification):
    """
    Handle CDC notifications from PostgreSQL
    This endpoint receives notifications when hitl_finished_at is updated
    """
    try:
        logger.info(f"Received CDC notification: {notification}")
        
        # Trigger sync for the affected document
        if notification.document_id:
            task_id = f"cdc_sync_{notification.document_id}_{int(time.time())}"
            active_syncs[task_id] = {
                "status": "pending",
                "document_id": notification.document_id,
                "trigger": "cdc",
                "field_name": notification.field_name
            }
            
            # Schedule background sync
            asyncio.create_task(_sync_document_background(task_id, notification.document_id))
            
            return {
                "message": "CDC notification processed",
                "task_id": task_id,
                "document_id": notification.document_id
            }
        
        return {"message": "CDC notification received but no action needed"}
        
    except Exception as e:
        logger.error(f"CDC notification processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"CDC processing failed: {str(e)}")


@app.get("/query/examples")
async def get_query_examples():
    """Get example queries for the GraphRAG system"""
    examples = [
        {
            "question": 'Has "ABC Trading Co" ever sent "Automobile parts" to "Shanghai Port"?',
            "description": "Check if a specific shipper has sent a specific product to a specific destination"
        },
        {
            "question": 'Is "XYZ Import Export" high risk?',
            "description": "Risk assessment based on shipment patterns"
        },
        {
            "question": "What products did Global Logistics Inc send?",
            "description": "List all products sent by a specific company"
        },
        {
            "question": "How many documents are in the system?",
            "description": "Get total document count"
        },
        {
            "question": "List all shippers",
            "description": "Get all legal entities with shipment counts"
        },
        {
            "question": "Find documents for ABC Trading",
            "description": "Search for documents related to a specific entity"
        },
        {
            "question": "Which customers process the most documents?",
            "description": "Get customers ranked by document processing volume"
        }
    ]
    
    return {"examples": examples}


# Background tasks
async def _sync_document_background(task_id: str, document_id: int):
    """Background task to sync a single document"""
    try:
        active_syncs[task_id]["status"] = "running"
        active_syncs[task_id]["started_at"] = time.time()
        
        sync.sync_single_document(document_id)
        
        active_syncs[task_id]["status"] = "completed"
        active_syncs[task_id]["completed_at"] = time.time()
        
        logger.info(f"Background sync completed for document {document_id}")
        
    except Exception as e:
        logger.error(f"Background sync failed for document {document_id}: {e}")
        active_syncs[task_id]["status"] = "failed"
        active_syncs[task_id]["error"] = str(e)
        active_syncs[task_id]["completed_at"] = time.time()


async def _sync_all_background(task_id: str):
    """Background task to sync all documents"""
    try:
        active_syncs[task_id]["status"] = "running"
        active_syncs[task_id]["started_at"] = time.time()
        
        sync.sync_all_data()
        
        active_syncs[task_id]["status"] = "completed"
        active_syncs[task_id]["completed_at"] = time.time()
        
        logger.info("Background full sync completed")
        
    except Exception as e:
        logger.error(f"Background full sync failed: {e}")
        active_syncs[task_id]["status"] = "failed"
        active_syncs[task_id]["error"] = str(e)
        active_syncs[task_id]["completed_at"] = time.time()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
