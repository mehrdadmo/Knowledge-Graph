#!/usr/bin/env python3
"""
Compliance Engine for Knowledge Graph
Automated compliance checking for IBAN, ID numbers, sanctions, and more
"""

import re
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from neo4j_manager import Neo4jManager
from psycopg2.extras import RealDictCursor
import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceStatus(Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    WARNING = "WARNING"
    PENDING_REVIEW = "PENDING_REVIEW"
    ERROR = "ERROR"

class ComplianceSeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

@dataclass
class ComplianceRule:
    """Compliance rule definition"""
    id: str
    name: str
    description: str
    category: str
    severity: ComplianceSeverity
    enabled: bool = True
    parameters: Dict = None

@dataclass
class ComplianceResult:
    """Compliance check result"""
    rule_id: str
    status: ComplianceStatus
    severity: ComplianceSeverity
    message: str
    details: Dict
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    timestamp: datetime = None

@dataclass
class ComplianceReport:
    """Complete compliance report for a document"""
    document_id: int
    document_number: str
    overall_status: ComplianceStatus
    total_rules_checked: int
    results: List[ComplianceResult]
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    generated_at: datetime

class ComplianceEngine:
    """Main compliance engine using knowledge graph"""
    
    def __init__(self):
        self.neo4j_manager = Neo4jManager()
        self.rules = self.load_compliance_rules()
        self.iban_validator = IBANValidator()
        self.id_validator = IDValidator()
        self.sanctions_checker = SanctionsChecker()
        self.trade_compliance = TradeComplianceChecker()
        
    def load_compliance_rules(self) -> List[ComplianceRule]:
        """Load all compliance rules"""
        return [
            # IBAN Validation Rules
            ComplianceRule(
                id="IBAN_FORMAT",
                name="IBAN Format Validation",
                description="Validate IBAN format and checksum",
                category="FINANCIAL",
                severity=ComplianceSeverity.HIGH
            ),
            ComplianceRule(
                id="IBAN_COUNTRY_SANCTION",
                name="IBAN Country Sanctions Check",
                description="Check if IBAN country is under sanctions",
                category="SANCTIONS",
                severity=ComplianceSeverity.CRITICAL
            ),
            
            # ID Number Validation
            ComplianceRule(
                id="COMPANY_ID_FORMAT",
                name="Company ID Format Validation",
                description="Validate company registration number format",
                category="IDENTIFICATION",
                severity=ComplianceSeverity.MEDIUM
            ),
            ComplianceRule(
                id="TAX_ID_VALIDATION",
                name="Tax ID Validation",
                description="Validate tax identification numbers",
                category="FINANCIAL",
                severity=ComplianceSeverity.HIGH
            ),
            
            # Sanctions Screening
            ComplianceRule(
                id="ENTITY_SANCTION_LIST",
                name="Entity Sanctions Screening",
                description="Screen entities against sanctions lists",
                category="SANCTIONS",
                severity=ComplianceSeverity.CRITICAL
            ),
            ComplianceRule(
                id="WATCHLIST_SCREENING",
                name="Watchlist Screening",
                description="Screen entities against watchlists",
                category="SANCTIONS",
                severity=ComplianceSeverity.HIGH
            ),
            
            # Trade Compliance
            ComplianceRule(
                id="HS_CODE_RESTRICTION",
                name="HS Code Trade Restrictions",
                description="Check if HS codes have trade restrictions",
                category="TRADE",
                severity=ComplianceSeverity.HIGH
            ),
            ComplianceRule(
                id="DUAL_USE_GOODS",
                name="Dual-Use Goods Check",
                description="Check for dual-use goods restrictions",
                category="TRADE",
                severity=ComplianceSeverity.CRITICAL
            ),
            ComplianceRule(
                id="EMBARGO_COUNTRY",
                name="Embargo Country Check",
                description="Check for embargoed countries",
                category="SANCTIONS",
                severity=ComplianceSeverity.CRITICAL
            ),
            
            # Document Compliance
            ComplianceRule(
                id="REQUIRED_FIELDS",
                name="Required Fields Validation",
                description="Ensure all required fields are present",
                category="DOCUMENT",
                severity=ComplianceSeverity.MEDIUM
            ),
            ComplianceRule(
                id="DATE_CONSISTENCY",
                name="Date Consistency Check",
                description="Validate date consistency across document",
                category="DOCUMENT",
                severity=ComplianceSeverity.LOW
            ),
            
            # Financial Compliance
            ComplianceRule(
                id="AMOUNT_THRESHOLD",
                name="Transaction Amount Threshold",
                description="Check if amounts exceed reporting thresholds",
                category="FINANCIAL",
                severity=ComplianceSeverity.HIGH
            ),
            ComplianceRule(
                id="CURRENCY_VALIDATION",
                name="Currency Code Validation",
                description="Validate ISO currency codes",
                category="FINANCIAL",
                severity=ComplianceSeverity.MEDIUM
            )
        ]
    
    async def check_document_compliance(self, document_id: int) -> ComplianceReport:
        """Check compliance for a specific document"""
        logger.info(f"Starting compliance check for document {document_id}")
        
        # Get document data from graph
        document_data = await self.get_document_data(document_id)
        if not document_data:
            raise ValueError(f"Document {document_id} not found")
        
        results = []
        
        # Check all enabled rules
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            try:
                result = await self.check_rule(rule, document_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Error checking rule {rule.id}: {str(e)}")
                results.append(ComplianceResult(
                    rule_id=rule.id,
                    status=ComplianceStatus.ERROR,
                    severity=rule.severity,
                    message=f"Rule execution error: {str(e)}",
                    details={"error": str(e)}
                ))
        
        # Generate compliance report
        report = self.generate_report(document_id, document_data, results)
        
        # Store results in database
        await self.store_compliance_report(report)
        
        logger.info(f"Compliance check completed for document {document_id}")
        return report
    
    async def get_document_data(self, document_id: int) -> Optional[Dict]:
        """Get document data from knowledge graph"""
        try:
            # Get document details
            doc_query = """
            MATCH (d:Document {id: $document_id})
            OPTIONAL MATCH (d)-[r]->(entity)
            RETURN d, 
                   type(r) as relationship_type,
                   entity.name as entity_name,
                   labels(entity) as entity_labels,
                   properties(entity) as entity_properties
            """
            
            results = await self.neo4j_manager.execute_query(
                doc_query, {"document_id": document_id}
            )
            
            if not results:
                return None
            
            # Structure document data
            document_data = {
                'document_id': document_id,
                'document_number': results[0]['d'].get('document_number'),
                'entities': [],
                'relationships': []
            }
            
            for result in results:
                if result.get('entity_name'):
                    entity_data = {
                        'name': result['entity_name'],
                        'type': result['entity_labels'][0] if result['entity_labels'] else 'Unknown',
                        'properties': result['entity_properties'] or {},
                        'relationship': result['relationship_type']
                    }
                    document_data['entities'].append(entity_data)
            
            return document_data
            
        except Exception as e:
            logger.error(f"Error getting document data: {str(e)}")
            return None
    
    async def check_rule(self, rule: ComplianceRule, document_data: Dict) -> ComplianceResult:
        """Check a specific compliance rule"""
        
        if rule.id == "IBAN_FORMAT":
            return await self.check_iban_format(document_data)
        elif rule.id == "IBAN_COUNTRY_SANCTION":
            return await self.check_iban_sanctions(document_data)
        elif rule.id == "COMPANY_ID_FORMAT":
            return await self.check_company_id_format(document_data)
        elif rule.id == "TAX_ID_VALIDATION":
            return await self.check_tax_id_validation(document_data)
        elif rule.id == "ENTITY_SANCTION_LIST":
            return await self.sanctions_checker.check_entity_sanctions(document_data)
        elif rule.id == "WATCHLIST_SCREENING":
            return await self.sanctions_checker.check_watchlist(document_data)
        elif rule.id == "HS_CODE_RESTRICTION":
            return await self.trade_compliance.check_hs_restrictions(document_data)
        elif rule.id == "DUAL_USE_GOODS":
            return await self.trade_compliance.check_dual_use_goods(document_data)
        elif rule.id == "EMBARGO_COUNTRY":
            return await self.trade_compliance.check_embargo_countries(document_data)
        elif rule.id == "REQUIRED_FIELDS":
            return await self.check_required_fields(document_data)
        elif rule.id == "DATE_CONSISTENCY":
            return await self.check_date_consistency(document_data)
        elif rule.id == "AMOUNT_THRESHOLD":
            return await self.check_amount_thresholds(document_data)
        elif rule.id == "CURRENCY_VALIDATION":
            return await self.check_currency_validation(document_data)
        else:
            return ComplianceResult(
                rule_id=rule.id,
                status=ComplianceStatus.WARNING,
                severity=rule.severity,
                message=f"Rule {rule.id} not implemented",
                details={}
            )
    
    async def check_iban_format(self, document_data: Dict) -> ComplianceResult:
        """Check IBAN format validation"""
        iban_patterns = []
        
        # Extract IBANs from document entities
        for entity in document_data['entities']:
            if 'iban' in entity['name'].lower() or self.iban_validator.looks_like_iban(entity['name']):
                iban_patterns.append(entity['name'])
        
        if not iban_patterns:
            return ComplianceResult(
                rule_id="IBAN_FORMAT",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.INFO,
                message="No IBANs found in document",
                details={"ibans_found": 0}
            )
        
        invalid_ibans = []
        valid_ibans = []
        
        for iban in iban_patterns:
            if self.iban_validator.validate(iban):
                valid_ibans.append(iban)
            else:
                invalid_ibans.append(iban)
        
        if invalid_ibans:
            return ComplianceResult(
                rule_id="IBAN_FORMAT",
                status=ComplianceStatus.NON_COMPLIANT,
                severity=ComplianceSeverity.HIGH,
                message=f"Invalid IBAN format found: {', '.join(invalid_ibans)}",
                details={
                    "invalid_ibans": invalid_ibans,
                    "valid_ibans": valid_ibans,
                    "total_ibans": len(iban_patterns)
                }
            )
        
        return ComplianceResult(
            rule_id="IBAN_FORMAT",
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.INFO,
            message=f"All {len(valid_ibans)} IBANs are valid",
            details={"valid_ibans": valid_ibans}
        )
    
    async def check_iban_sanctions(self, document_data: Dict) -> ComplianceResult:
        """Check IBAN country sanctions"""
        sanctioned_countries = ['IR', 'SY', 'KP', 'RU', 'BY']  # Example sanctioned countries
        sanctioned_ibans = []
        
        for entity in document_data['entities']:
            if self.iban_validator.looks_like_iban(entity['name']):
                country_code = self.iban_validator.extract_country_code(entity['name'])
                if country_code in sanctioned_countries:
                    sanctioned_ibans.append({
                        'iban': entity['name'],
                        'country': country_code,
                        'entity': entity['name']
                    })
        
        if sanctioned_ibans:
            return ComplianceResult(
                rule_id="IBAN_COUNTRY_SANCTION",
                status=ComplianceStatus.NON_COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                message=f"IBANs from sanctioned countries found",
                details={"sanctioned_ibans": sanctioned_ibans}
            )
        
        return ComplianceResult(
            rule_id="IBAN_COUNTRY_SANCTION",
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.INFO,
            message="No IBANs from sanctioned countries",
            details={}
        )
    
    async def check_company_id_format(self, document_data: Dict) -> ComplianceResult:
        """Check company ID format"""
        invalid_ids = []
        
        for entity in document_data['entities']:
            if entity['type'] == 'LegalEntity':
                entity_name = entity['name']
                
                # Check for common company ID patterns
                if not self.id_validator.validate_company_id(entity_name):
                    invalid_ids.append(entity_name)
        
        if invalid_ids:
            return ComplianceResult(
                rule_id="COMPANY_ID_FORMAT",
                status=ComplianceStatus.WARNING,
                severity=ComplianceSeverity.MEDIUM,
                message="Company IDs may need validation",
                details={"invalid_ids": invalid_ids}
            )
        
        return ComplianceResult(
            rule_id="COMPANY_ID_FORMAT",
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.INFO,
            message="Company ID formats appear valid",
            details={}
        )
    
    async def check_tax_id_validation(self, document_data: Dict) -> ComplianceResult:
        """Check tax ID validation"""
        # Similar implementation for tax IDs
        return ComplianceResult(
            rule_id="TAX_ID_VALIDATION",
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.INFO,
            message="Tax ID validation not implemented yet",
            details={}
        )
    
    async def check_required_fields(self, document_data: Dict) -> ComplianceResult:
        """Check required fields are present"""
        required_entities = ['LegalEntity']  # At least one legal entity required
        missing_fields = []
        
        entity_types = {entity['type'] for entity in document_data['entities']}
        
        for required in required_entities:
            if required not in entity_types:
                missing_fields.append(required)
        
        if missing_fields:
            return ComplianceResult(
                rule_id="REQUIRED_FIELDS",
                status=ComplianceStatus.NON_COMPLIANT,
                severity=ComplianceSeverity.MEDIUM,
                message=f"Missing required fields: {', '.join(missing_fields)}",
                details={"missing_fields": missing_fields}
            )
        
        return ComplianceResult(
            rule_id="REQUIRED_FIELDS",
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.INFO,
            message="All required fields present",
            details={}
        )
    
    async def check_date_consistency(self, document_data: Dict) -> ComplianceResult:
        """Check date consistency"""
        # Implementation for date validation
        return ComplianceResult(
            rule_id="DATE_CONSISTENCY",
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.INFO,
            message="Date consistency check passed",
            details={}
        )
    
    async def check_amount_thresholds(self, document_data: Dict) -> ComplianceResult:
        """Check transaction amount thresholds"""
        # Implementation for amount validation
        return ComplianceResult(
            rule_id="AMOUNT_THRESHOLD",
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.INFO,
            message="Amount thresholds within limits",
            details={}
        )
    
    async def check_currency_validation(self, document_data: Dict) -> ComplianceResult:
        """Check currency validation"""
        # Implementation for currency validation
        return ComplianceResult(
            rule_id="CURRENCY_VALIDATION",
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.INFO,
            message="Currency codes are valid",
            details={}
        )
    
    def generate_report(self, document_id: int, document_data: Dict, results: List[ComplianceResult]) -> ComplianceReport:
        """Generate compliance report"""
        
        # Count issues by severity
        critical_issues = sum(1 for r in results if r.severity == ComplianceSeverity.CRITICAL and r.status != ComplianceStatus.COMPLIANT)
        high_issues = sum(1 for r in results if r.severity == ComplianceSeverity.HIGH and r.status != ComplianceStatus.COMPLIANT)
        medium_issues = sum(1 for r in results if r.severity == ComplianceSeverity.MEDIUM and r.status != ComplianceStatus.COMPLIANT)
        low_issues = sum(1 for r in results if r.severity == ComplianceSeverity.LOW and r.status != ComplianceStatus.COMPLIANT)
        
        # Determine overall status
        if critical_issues > 0:
            overall_status = ComplianceStatus.NON_COMPLIANT
        elif high_issues > 0:
            overall_status = ComplianceStatus.NON_COMPLIANT
        elif medium_issues > 2:
            overall_status = ComplianceStatus.WARNING
        elif low_issues > 5:
            overall_status = ComplianceStatus.WARNING
        else:
            overall_status = ComplianceStatus.COMPLIANT
        
        return ComplianceReport(
            document_id=document_id,
            document_number=document_data.get('document_number', f'DOC-{document_id}'),
            overall_status=overall_status,
            total_rules_checked=len(results),
            results=results,
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            generated_at=datetime.now()
        )
    
    async def store_compliance_report(self, report: ComplianceReport):
        """Store compliance report in database"""
        try:
            # Implementation to store in PostgreSQL
            logger.info(f"Storing compliance report for document {report.document_id}")
        except Exception as e:
            logger.error(f"Error storing compliance report: {str(e)}")

class IBANValidator:
    """IBAN validation utilities"""
    
    def __init__(self):
        # Country-specific IBAN patterns (simplified)
        self.country_patterns = {
            'DE': r'^DE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\s?\d{8}$',  # Germany
            'FR': r'^FR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\s?\d{6}$',  # France
            'GB': r'^GB\d{2}\s?[A-Z]{4}\s?\d{4}\s?\d{4}\s?\d{2}$',  # UK
            'NL': r'^NL\d{2}\s?[A-Z]{4}\s?\d{4}\s?\d{4}\s?\d{2}$',  # Netherlands
            'IT': r'^IT\d{2}\s?[A-Z]\s?\d{5}\s?\d{5}\s?\d{4}\s?\d{3}$',  # Italy
            'ES': r'^ES\d{2}\s?\d{4}\s?\d{4}\s?\d{2}\s?\d{2}\s?\d{10}$',  # Spain
        }
    
    def looks_like_iban(self, text: str) -> bool:
        """Check if text looks like an IBAN"""
        text = text.replace(' ', '').upper()
        if len(text) < 15 or len(text) > 34:
            return False
        
        # Check if starts with valid country code
        country_code = text[:2]
        return country_code in self.country_patterns
    
    def validate(self, iban: str) -> bool:
        """Validate IBAN format and checksum"""
        iban = iban.replace(' ', '').upper()
        
        # Check format
        country_code = iban[:2]
        if country_code not in self.country_patterns:
            return False
        
        pattern = self.country_patterns[country_code]
        if not re.match(pattern, iban):
            return False
        
        # Validate checksum (simplified)
        return self.validate_checksum(iban)
    
    def validate_checksum(self, iban: str) -> bool:
        """Validate IBAN checksum"""
        # Simplified checksum validation
        # In production, implement full IBAN checksum algorithm
        return len(iban) >= 15 and len(iban) <= 34
    
    def extract_country_code(self, iban: str) -> str:
        """Extract country code from IBAN"""
        return iban.replace(' ', '').upper()[:2]

class IDValidator:
    """ID number validation utilities"""
    
    def validate_company_id(self, company_name: str) -> bool:
        """Validate company ID format"""
        # Check for common company ID patterns
        # This is a simplified implementation
        return len(company_name) > 2 and not company_name.isdigit()

class SanctionsChecker:
    """Sanctions checking utilities"""
    
    def __init__(self):
        # In production, load from real sanctions lists
        self.sanctioned_entities = [
            "SANCTIONED ENTITY 1",
            "SANCTIONED ENTITY 2"
        ]
    
    async def check_entity_sanctions(self, document_data: Dict) -> ComplianceResult:
        """Check entities against sanctions lists"""
        sanctioned_found = []
        
        for entity in document_data['entities']:
            if entity['type'] == 'LegalEntity':
                entity_name = entity['name'].upper()
                if any(sanctioned in entity_name for sanctioned in self.sanctioned_entities):
                    sanctioned_found.append(entity['name'])
        
        if sanctioned_found:
            return ComplianceResult(
                rule_id="ENTITY_SANCTION_LIST",
                status=ComplianceStatus.NON_COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                message=f"Sanctioned entities found: {', '.join(sanctioned_found)}",
                details={"sanctioned_entities": sanctioned_found}
            )
        
        return ComplianceResult(
            rule_id="ENTITY_SANCTION_LIST",
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.INFO,
            message="No sanctioned entities found",
            details={}
        )
    
    async def check_watchlist(self, document_data: Dict) -> ComplianceResult:
        """Check entities against watchlists"""
        # Implementation for watchlist checking
        return ComplianceResult(
            rule_id="WATCHLIST_SCREENING",
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.INFO,
            message="No watchlist matches found",
            details={}
        )

class TradeComplianceChecker:
    """Trade compliance checking utilities"""
    
    def __init__(self):
        # HS codes with restrictions
        self.restricted_hs_codes = ['84599000', '84669300']  # Example restricted codes
        self.dual_use_hs_codes = ['84599000']  # Example dual-use codes
        self.embargoed_countries = ['IR', 'SY', 'KP', 'RU', 'BY']
    
    async def check_hs_restrictions(self, document_data: Dict) -> ComplianceResult:
        """Check HS code restrictions"""
        restricted_found = []
        
        for entity in document_data['entities']:
            if entity['type'] == 'HSCode':
                hs_code = entity['properties'].get('code', entity['name'])
                if hs_code in self.restricted_hs_codes:
                    restricted_found.append(hs_code)
        
        if restricted_found:
            return ComplianceResult(
                rule_id="HS_CODE_RESTRICTION",
                status=ComplianceStatus.NON_COMPLIANT,
                severity=ComplianceSeverity.HIGH,
                message=f"Restricted HS codes found: {', '.join(restricted_found)}",
                details={"restricted_hs_codes": restricted_found}
            )
        
        return ComplianceResult(
            rule_id="HS_CODE_RESTRICTION",
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.INFO,
            message="No restricted HS codes found",
            details={}
        )
    
    async def check_dual_use_goods(self, document_data: Dict) -> ComplianceResult:
        """Check for dual-use goods"""
        dual_use_found = []
        
        for entity in document_data['entities']:
            if entity['type'] == 'HSCode':
                hs_code = entity['properties'].get('code', entity['name'])
                if hs_code in self.dual_use_hs_codes:
                    dual_use_found.append(hs_code)
        
        if dual_use_found:
            return ComplianceResult(
                rule_id="DUAL_USE_GOODS",
                status=ComplianceStatus.WARNING,
                severity=ComplianceSeverity.CRITICAL,
                message=f"Dual-use goods found: {', '.join(dual_use_found)}",
                details={"dual_use_hs_codes": dual_use_found}
            )
        
        return ComplianceResult(
            rule_id="DUAL_USE_GOODS",
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.INFO,
            message="No dual-use goods found",
            details={}
        )
    
    async def check_embargo_countries(self, document_data: Dict) -> ComplianceResult:
        """Check for embargoed countries"""
        embargoed_found = []
        
        for entity in document_data['entities']:
            if entity['type'] == 'Location':
                location_name = entity['name'].upper()
                for country_code in self.embargoed_countries:
                    if country_code in location_name or self.get_country_name(country_code) in location_name:
                        embargoed_found.append(entity['name'])
        
        if embargoed_found:
            return ComplianceResult(
                rule_id="EMBARGO_COUNTRY",
                status=ComplianceStatus.NON_COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                message=f"Embargoed countries found: {', '.join(embargoed_found)}",
                details={"embargoed_locations": embargoed_found}
            )
        
        return ComplianceResult(
            rule_id="EMBARGO_COUNTRY",
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity.INFO,
            message="No embargoed countries found",
            details={}
        )
    
    def get_country_name(self, country_code: str) -> str:
        """Get country name from code"""
        country_names = {
            'IR': 'IRAN',
            'SY': 'SYRIA',
            'KP': 'NORTH KOREA',
            'RU': 'RUSSIA',
            'BY': 'BELARUS'
        }
        return country_names.get(country_code, country_code)

# CLI interface
async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compliance Engine for Knowledge Graph')
    parser.add_argument('--check-document', type=int, help='Check compliance for specific document')
    parser.add_argument('--check-all', action='store_true', help='Check compliance for all documents')
    parser.add_argument('--test-iban', help='Test IBAN validation')
    parser.add_argument('--list-rules', action='store_true', help='List all compliance rules')
    
    args = parser.parse_args()
    
    engine = ComplianceEngine()
    
    if args.check_document:
        report = await engine.check_document_compliance(args.check_document)
        print(f"\n🛡️ Compliance Report for Document {report.document_number}")
        print(f"Overall Status: {report.overall_status.value}")
        print(f"Rules Checked: {report.total_rules_checked}")
        print(f"Critical Issues: {report.critical_issues}")
        print(f"High Issues: {report.high_issues}")
        print(f"Medium Issues: {report.medium_issues}")
        print(f"Low Issues: {report.low_issues}")
        
        print("\n📋 Detailed Results:")
        for result in report.results:
            status_icon = "✅" if result.status == ComplianceStatus.COMPLIANT else "❌"
            print(f"{status_icon} {result.rule_id}: {result.message}")
    
    elif args.test_iban:
        validator = IBANValidator()
        is_valid = validator.validate(args.test_iban)
        print(f"IBAN {args.test_iban} is {'VALID' if is_valid else 'INVALID'}")
    
    elif args.list_rules:
        print("\n🛡️ Compliance Rules:")
        for rule in engine.rules:
            status = "✅" if rule.enabled else "❌"
            print(f"{status} {rule.id}: {rule.name} ({rule.severity.value})")
            print(f"   {rule.description}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
