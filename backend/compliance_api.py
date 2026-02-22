#!/usr/bin/env python3
"""
Compliance Engine FastAPI Endpoints
REST API for compliance checking and monitoring
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging

from compliance_engine import ComplianceEngine, ComplianceReport, ComplianceStatus, ComplianceSeverity
from neo4j_manager import Neo4jManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class ComplianceCheckRequest(BaseModel):
    document_id: int = Field(..., description="Document ID to check")
    force_recheck: bool = Field(False, description="Force recheck even if recently checked")

class ComplianceCheckResponse(BaseModel):
    document_id: int
    document_number: str
    overall_status: str
    total_rules_checked: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    generated_at: datetime
    results: List[Dict[str, Any]]

class IBANValidationRequest(BaseModel):
    iban: str = Field(..., description="IBAN to validate")

class IBANValidationResponse(BaseModel):
    iban: str
    is_valid: bool
    country_code: str
    message: str

class ComplianceRuleResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    severity: str
    enabled: bool

class ComplianceStatisticsResponse(BaseModel):
    total_documents: int
    compliant_documents: int
    non_compliant_documents: int
    warning_documents: int
    pending_documents: int
    compliance_percentage: float
    total_critical_issues: int
    total_high_issues: int
    total_medium_issues: int
    total_low_issues: int

class ComplianceAlertResponse(BaseModel):
    id: int
    document_id: int
    alert_type: str
    severity: str
    title: str
    message: str
    status: str
    created_at: datetime

# Initialize FastAPI app
app = FastAPI(
    title="Compliance Engine API",
    description="Automated compliance checking for trade documents",
    version="1.0.0"
)

# Global compliance engine instance
compliance_engine = ComplianceEngine()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Compliance Engine API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Neo4j connection
        neo4j_manager = Neo4jManager()
        stats = neo4j_manager.get_graph_statistics()
        
        return {
            "status": "healthy",
            "neo4j_connected": True,
            "graph_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/compliance/check", response_model=ComplianceCheckResponse)
async def check_compliance(
    request: ComplianceCheckRequest,
    background_tasks: BackgroundTasks
):
    """Check compliance for a specific document"""
    try:
        logger.info(f"Starting compliance check for document {request.document_id}")
        
        # Check if document exists
        document_data = await compliance_engine.get_document_data(request.document_id)
        if not document_data:
            raise HTTPException(status_code=404, detail=f"Document {request.document_id} not found")
        
        # Run compliance check
        report = await compliance_engine.check_document_compliance(request.document_id)
        
        # Convert results to response format
        results = []
        for result in report.results:
            results.append({
                "rule_id": result.rule_id,
                "status": result.status.value,
                "severity": result.severity.value,
                "message": result.message,
                "details": result.details,
                "entity_id": result.entity_id,
                "entity_type": result.entity_type
            })
        
        response = ComplianceCheckResponse(
            document_id=report.document_id,
            document_number=report.document_number,
            overall_status=report.overall_status.value,
            total_rules_checked=report.total_rules_checked,
            critical_issues=report.critical_issues,
            high_issues=report.high_issues,
            medium_issues=report.medium_issues,
            low_issues=report.low_issues,
            generated_at=report.generated_at,
            results=results
        )
        
        # Log compliance check completion
        logger.info(f"Compliance check completed for document {request.document_id}: {report.overall_status.value}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compliance check failed for document {request.document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {str(e)}")

@app.post("/compliance/batch-check")
async def batch_check_compliance(
    document_ids: List[int],
    background_tasks: BackgroundTasks
):
    """Check compliance for multiple documents"""
    try:
        logger.info(f"Starting batch compliance check for {len(document_ids)} documents")
        
        results = []
        errors = []
        
        for doc_id in document_ids:
            try:
                report = await compliance_engine.check_document_compliance(doc_id)
                results.append({
                    "document_id": doc_id,
                    "status": "success",
                    "overall_status": report.overall_status.value,
                    "critical_issues": report.critical_issues,
                    "high_issues": report.high_issues,
                    "medium_issues": report.medium_issues,
                    "low_issues": report.low_issues
                })
            except Exception as e:
                errors.append({
                    "document_id": doc_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "total_documents": len(document_ids),
            "successful_checks": len(results),
            "failed_checks": len(errors),
            "results": results,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch compliance check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch compliance check failed: {str(e)}")

@app.post("/validation/iban", response_model=IBANValidationResponse)
async def validate_iban(request: IBANValidationRequest):
    """Validate IBAN format and checksum"""
    try:
        from compliance_engine import IBANValidator
        
        validator = IBANValidator()
        is_valid = validator.validate(request.iban)
        country_code = validator.extract_country_code(request.iban)
        
        message = "IBAN is valid" if is_valid else "IBAN format is invalid"
        
        return IBANValidationResponse(
            iban=request.iban,
            is_valid=is_valid,
            country_code=country_code,
            message=message
        )
        
    except Exception as e:
        logger.error(f"IBAN validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"IBAN validation failed: {str(e)}")

@app.get("/compliance/rules", response_model=List[ComplianceRuleResponse])
async def get_compliance_rules():
    """Get all compliance rules"""
    try:
        rules = []
        for rule in compliance_engine.rules:
            rules.append(ComplianceRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                category=rule.category,
                severity=rule.severity.value,
                enabled=rule.enabled
            ))
        
        return rules
        
    except Exception as e:
        logger.error(f"Failed to get compliance rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get compliance rules: {str(e)}")

@app.put("/compliance/rules/{rule_id}/toggle")
async def toggle_compliance_rule(rule_id: str):
    """Enable/disable a compliance rule"""
    try:
        # Find the rule
        rule = None
        for r in compliance_engine.rules:
            if r.id == rule_id:
                rule = r
                break
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        # Toggle rule
        rule.enabled = not rule.enabled
        
        return {
            "rule_id": rule_id,
            "enabled": rule.enabled,
            "message": f"Rule {rule_id} {'enabled' if rule.enabled else 'disabled'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle rule {rule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle rule: {str(e)}")

@app.get("/compliance/statistics", response_model=ComplianceStatisticsResponse)
async def get_compliance_statistics():
    """Get compliance statistics"""
    try:
        # This would typically query the database
        # For now, return mock statistics
        return ComplianceStatisticsResponse(
            total_documents=100,
            compliant_documents=85,
            non_compliant_documents=10,
            warning_documents=3,
            pending_documents=2,
            compliance_percentage=85.0,
            total_critical_issues=5,
            total_high_issues=15,
            total_medium_issues=25,
            total_low_issues=40
        )
        
    except Exception as e:
        logger.error(f"Failed to get compliance statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get compliance statistics: {str(e)}")

@app.get("/compliance/alerts", response_model=List[ComplianceAlertResponse])
async def get_compliance_alerts(
    status: Optional[str] = Query(None, description="Filter by alert status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=1000, description="Number of alerts to return")
):
    """Get compliance alerts"""
    try:
        # This would typically query the database
        # For now, return mock alerts
        alerts = [
            ComplianceAlertResponse(
                id=1,
                document_id=123,
                alert_type="COMPLIANCE_VIOLATION",
                severity="CRITICAL",
                title="Sanctioned Entity Detected",
                message="Document contains entity from sanctioned country",
                status="OPEN",
                created_at=datetime.now() - timedelta(hours=2)
            ),
            ComplianceAlertResponse(
                id=2,
                document_id=124,
                alert_type="COMPLIANCE_VIOLATION",
                severity="HIGH",
                title="Invalid IBAN Format",
                message="IBAN format validation failed",
                status="OPEN",
                created_at=datetime.now() - timedelta(hours=4)
            )
        ]
        
        # Apply filters
        if status:
            alerts = [a for a in alerts if a.status == status]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts[:limit]
        
    except Exception as e:
        logger.error(f"Failed to get compliance alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get compliance alerts: {str(e)}")

@app.put("/compliance/alerts/{alert_id}/acknowledge")
async def acknowledge_compliance_alert(alert_id: int):
    """Acknowledge a compliance alert"""
    try:
        # This would typically update the database
        return {
            "alert_id": alert_id,
            "status": "ACKNOWLEDGED",
            "message": f"Alert {alert_id} acknowledged"
        }
        
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

@app.put("/compliance/alerts/{alert_id}/resolve")
async def resolve_compliance_alert(alert_id: int, resolution_note: str = ""):
    """Resolve a compliance alert"""
    try:
        # This would typically update the database
        return {
            "alert_id": alert_id,
            "status": "RESOLVED",
            "resolution_note": resolution_note,
            "message": f"Alert {alert_id} resolved"
        }
        
    except Exception as e:
        logger.error(f"Failed to resolve alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")

@app.get("/compliance/dashboard")
async def get_compliance_dashboard():
    """Get compliance dashboard data"""
    try:
        # This would typically query the database views
        return {
            "summary": {
                "total_documents": 100,
                "compliant_percentage": 85.0,
                "critical_alerts": 3,
                "high_alerts": 7,
                "medium_alerts": 12,
                "low_alerts": 25
            },
            "recent_violations": [
                {
                    "document_id": 123,
                    "document_number": "DOC-001",
                    "violation_type": "SANCTIONED_ENTITY",
                    "severity": "CRITICAL",
                    "detected_at": datetime.now() - timedelta(hours=2)
                },
                {
                    "document_id": 124,
                    "document_number": "DOC-002",
                    "violation_type": "INVALID_IBAN",
                    "severity": "HIGH",
                    "detected_at": datetime.now() - timedelta(hours=4)
                }
            ],
            "trends": {
                "daily_compliance": [
                    {"date": "2024-02-20", "percentage": 82.0},
                    {"date": "2024-02-21", "percentage": 84.0},
                    {"date": "2024-02-22", "percentage": 85.0}
                ],
                "alert_trends": [
                    {"date": "2024-02-20", "critical": 2, "high": 5, "medium": 10},
                    {"date": "2024-02-21", "critical": 3, "high": 6, "medium": 11},
                    {"date": "2024-02-22", "critical": 3, "high": 7, "medium": 12}
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get compliance dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get compliance dashboard: {str(e)}")

@app.post("/compliance/sanctions/update")
async def update_sanctions_lists(background_tasks: BackgroundTasks):
    """Update sanctions lists from external sources"""
    try:
        # This would typically fetch from external APIs
        background_tasks.add_task(update_sanctions_data)
        
        return {
            "message": "Sanctions list update started",
            "status": "IN_PROGRESS"
        }
        
    except Exception as e:
        logger.error(f"Failed to start sanctions update: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start sanctions update: {str(e)}")

async def update_sanctions_data():
    """Background task to update sanctions data"""
    logger.info("Starting sanctions list update")
    # Implementation would fetch from external APIs
    logger.info("Sanctions list update completed")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found", "message": str(exc.detail)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
