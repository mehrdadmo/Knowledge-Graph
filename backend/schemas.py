from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question about the knowledge graph")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")


class QueryResponse(BaseModel):
    question: str
    answer: str
    cypher_query: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
    execution_time_ms: Optional[float] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class EntityExtraction(BaseModel):
    entities: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)


class CDCNotification(BaseModel):
    document_id: int
    field_id: Optional[int] = None
    field_name: Optional[str] = None
    hitl_value: Optional[str] = None
    finished_at: Optional[datetime] = None
    customer_id: Optional[int] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    created_at: Optional[datetime] = None


class SyncStatus(BaseModel):
    status: str
    last_sync: Optional[datetime] = None
    total_documents: int = 0
    synced_documents: int = 0
    pending_syncs: int = 0
