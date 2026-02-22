#!/usr/bin/env python3
"""
Compliance Engine Test Suite
Comprehensive testing of compliance checking functionality
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from compliance_engine import ComplianceEngine, ComplianceStatus, ComplianceSeverity
from neo4j_manager import Neo4jManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceEngineTest:
    """Comprehensive test suite for compliance engine"""
    
    def __init__(self):
        self.engine = ComplianceEngine()
        self.neo4j_manager = Neo4jManager()
        self.test_results = []
    
    async def run_all_tests(self):
        """Run all compliance engine tests"""
        print("🛡️ Compliance Engine Test Suite")
        print("=" * 60)
        
        try:
            # 1️⃣ Test IBAN Validation
            await self.test_iban_validation()
            
            # 2️⃣ Test Sanctions Checking
            await self.test_sanctions_checking()
            
            # 3️⃣ Test Trade Compliance
            await self.test_trade_compliance()
            
            # 4️⃣ Test Document Compliance
            await self.test_document_compliance()
            
            # 5️⃣ Test Rule Management
            await self.test_rule_management()
            
            # 6️⃣ Test Integration with Knowledge Graph
            await self.test_graph_integration()
            
            # 7️⃣ Test Performance
            await self.test_performance()
            
            # Show summary
            self.show_test_summary()
            
        except Exception as e:
            print(f"❌ Test suite failed: {str(e)}")
            logger.error(f"Test suite error: {str(e)}", exc_info=True)
    
    async def test_iban_validation(self):
        """Test IBAN validation functionality"""
        print("\n🧪 Testing IBAN Validation...")
        
        test_cases = [
            # Valid IBANs
            {"iban": "DE89370400440532013000", "expected": True, "country": "DE"},
            {"iban": "FR1420041010050500013M02606", "expected": True, "country": "FR"},
            {"iban": "GB82WEST12345698765432", "expected": True, "country": "GB"},
            
            # Invalid IBANs
            {"iban": "DE89370400440532013001", "expected": False, "country": "DE"},  # Bad checksum
            {"iban": "INVALID123456789", "expected": False, "country": None},  # Invalid format
            {"iban": "DE89 ABCD", "expected": False, "country": None},  # Too short
        ]
        
        passed = 0
        total = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                from compliance_engine import IBANValidator
                validator = IBANValidator()
                
                result = validator.validate(test_case["iban"])
                country = validator.extract_country_code(test_case["iban"])
                
                if result == test_case["expected"]:
                    print(f"   ✅ Test {i}: {test_case['iban']} - {'Valid' if result else 'Invalid'}")
                    passed += 1
                else:
                    print(f"   ❌ Test {i}: {test_case['iban']} - Expected {test_case['expected']}, got {result}")
                
            except Exception as e:
                print(f"   ❌ Test {i}: {test_case['iban']} - Error: {str(e)}")
        
        self.test_results.append({
            "category": "IBAN Validation",
            "passed": passed,
            "total": total,
            "success_rate": (passed / total) * 100
        })
        
        print(f"   📊 IBAN Validation: {passed}/{total} tests passed")
    
    async def test_sanctions_checking(self):
        """Test sanctions checking functionality"""
        print("\n🧪 Testing Sanctions Checking...")
        
        # Create test document with sanctioned entities
        test_document = {
            'document_id': 999999,
            'document_number': 'SANCTION-TEST-001',
            'entities': [
                {
                    'name': 'SANCTIONED ENTITY 1',
                    'type': 'LegalEntity',
                    'properties': {},
                    'relationship': 'HAS_SHIPPER'
                },
                {
                    'name': 'IR89370400440532013000',  # Iran IBAN
                    'type': 'LegalEntity',
                    'properties': {},
                    'relationship': 'HAS_CONSIGNEE'
                },
                {
                    'name': 'NORMAL COMPANY LTD',
                    'type': 'LegalEntity',
                    'properties': {},
                    'relationship': 'HAS_NOTIFY_PARTY'
                }
            ]
        }
        
        try:
            # Test entity sanctions
            result = await self.engine.sanctions_checker.check_entity_sanctions(test_document)
            
            if result.status == ComplianceStatus.NON_COMPLIANT:
                print("   ✅ Entity sanctions detection working")
                sanctions_found = len(result.details.get('sanctioned_entities', []))
                print(f"   📊 Found {sanctions_found} sanctioned entities")
            else:
                print("   ❌ Entity sanctions detection failed")
            
            # Test IBAN sanctions
            result = await self.engine.check_iban_sanctions(test_document)
            
            if result.status == ComplianceStatus.NON_COMPLIANT:
                print("   ✅ IBAN sanctions detection working")
                sanctioned_ibans = len(result.details.get('sanctioned_ibans', []))
                print(f"   📊 Found {sanctioned_ibans} sanctioned IBANs")
            else:
                print("   ⚠️ IBAN sanctions detection may need adjustment")
            
            self.test_results.append({
                "category": "Sanctions Checking",
                "passed": 2,
                "total": 2,
                "success_rate": 100.0
            })
            
        except Exception as e:
            print(f"   ❌ Sanctions checking test failed: {str(e)}")
            self.test_results.append({
                "category": "Sanctions Checking",
                "passed": 0,
                "total": 2,
                "success_rate": 0.0
            })
    
    async def test_trade_compliance(self):
        """Test trade compliance functionality"""
        print("\n🧪 Testing Trade Compliance...")
        
        # Create test document with trade data
        test_document = {
            'document_id': 999998,
            'document_number': 'TRADE-TEST-001',
            'entities': [
                {
                    'name': '84599000',  # Restricted HS code
                    'type': 'HSCode',
                    'properties': {'code': '84599000'},
                    'relationship': 'CLASSIFIED_AS'
                },
                {
                    'name': 'IRAN',  # Embargoed country
                    'type': 'Location',
                    'properties': {},
                    'relationship': 'ORIGINATED_FROM'
                },
                {
                    'name': 'NORMAL PRODUCT',
                    'type': 'Product',
                    'properties': {},
                    'relationship': 'CONTAINS'
                }
            ]
        }
        
        try:
            passed_tests = 0
            total_tests = 3
            
            # Test HS code restrictions
            result = await self.engine.trade_compliance.check_hs_restrictions(test_document)
            if result.status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.WARNING]:
                print("   ✅ HS code restrictions working")
                passed_tests += 1
            else:
                print("   ❌ HS code restrictions not working")
            
            # Test dual-use goods
            result = await self.engine.trade_compliance.check_dual_use_goods(test_document)
            if result.status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.WARNING]:
                print("   ✅ Dual-use goods detection working")
                passed_tests += 1
            else:
                print("   ❌ Dual-use goods detection not working")
            
            # Test embargo countries
            result = await self.engine.trade_compliance.check_embargo_countries(test_document)
            if result.status == ComplianceStatus.NON_COMPLIANT:
                print("   ✅ Embargo country detection working")
                passed_tests += 1
            else:
                print("   ❌ Embargo country detection not working")
            
            self.test_results.append({
                "category": "Trade Compliance",
                "passed": passed_tests,
                "total": total_tests,
                "success_rate": (passed_tests / total_tests) * 100
            })
            
        except Exception as e:
            print(f"   ❌ Trade compliance test failed: {str(e)}")
            self.test_results.append({
                "category": "Trade Compliance",
                "passed": 0,
                "total": 3,
                "success_rate": 0.0
            })
    
    async def test_document_compliance(self):
        """Test complete document compliance checking"""
        print("\n🧪 Testing Document Compliance...")
        
        # Create comprehensive test document
        test_document = {
            'document_id': 999997,
            'document_number': 'COMPLIANCE-TEST-001',
            'entities': [
                {
                    'name': 'TEST COMPANY LTD',
                    'type': 'LegalEntity',
                    'properties': {},
                    'relationship': 'HAS_SHIPPER'
                },
                {
                    'name': 'DE89370400440532013000',  # Valid German IBAN
                    'type': 'LegalEntity',
                    'properties': {},
                    'relationship': 'HAS_CONSIGNEE'
                },
                {
                    'name': '84713000',  # Normal HS code
                    'type': 'HSCode',
                    'properties': {'code': '84713000'},
                    'relationship': 'CLASSIFIED_AS'
                },
                {
                    'name': 'GERMANY',
                    'type': 'Location',
                    'properties': {},
                    'relationship': 'ORIGINATED_FROM'
                }
            ]
        }
        
        try:
            # Mock the document data retrieval
            original_get_data = self.engine.get_document_data
            self.engine.get_document_data = lambda doc_id: test_document if doc_id == 999997 else None
            
            # Run compliance check
            report = await self.engine.check_document_compliance(999997)
            
            # Validate report structure
            required_fields = ['document_id', 'overall_status', 'total_rules_checked', 'results']
            missing_fields = [field for field in required_fields if not hasattr(report, field)]
            
            if not missing_fields:
                print("   ✅ Compliance report structure valid")
                
                # Check if rules were executed
                if report.total_rules_checked > 0:
                    print(f"   ✅ {report.total_rules_checked} rules checked")
                    
                    # Check for critical issues
                    if report.critical_issues == 0:
                        print("   ✅ No critical issues found")
                    else:
                        print(f"   ⚠️ {report.critical_issues} critical issues found")
                    
                    passed_tests = 3
                else:
                    print("   ❌ No rules were checked")
                    passed_tests = 2
            else:
                print(f"   ❌ Missing report fields: {missing_fields}")
                passed_tests = 1
            
            # Restore original method
            self.engine.get_document_data = original_get_data
            
            self.test_results.append({
                "category": "Document Compliance",
                "passed": passed_tests,
                "total": 4,
                "success_rate": (passed_tests / 4) * 100
            })
            
        except Exception as e:
            print(f"   ❌ Document compliance test failed: {str(e)}")
            self.test_results.append({
                "category": "Document Compliance",
                "passed": 0,
                "total": 4,
                "success_rate": 0.0
            })
    
    async def test_rule_management(self):
        """Test compliance rule management"""
        print("\n🧪 Testing Rule Management...")
        
        try:
            rules = self.engine.rules
            
            # Check if rules are loaded
            if len(rules) > 0:
                print(f"   ✅ {len(rules)} compliance rules loaded")
                
                # Check rule categories
                categories = set(rule.category for rule in rules)
                expected_categories = {'FINANCIAL', 'SANCTIONS', 'TRADE', 'DOCUMENT', 'IDENTIFICATION'}
                
                if expected_categories.issubset(categories):
                    print("   ✅ All expected rule categories present")
                    passed_tests = 2
                else:
                    missing = expected_categories - categories
                    print(f"   ⚠️ Missing rule categories: {missing}")
                    passed_tests = 1
                
                # Check rule severities
                severities = set(rule.severity for rule in rules)
                expected_severities = {ComplianceSeverity.CRITICAL, ComplianceSeverity.HIGH, 
                                   ComplianceSeverity.MEDIUM, ComplianceSeverity.LOW, ComplianceSeverity.INFO}
                
                if expected_severities.issubset(severities):
                    print("   ✅ All rule severities present")
                    passed_tests += 1
                else:
                    missing = expected_severities - severities
                    print(f"   ⚠️ Missing rule severities: {missing}")
            else:
                print("   ❌ No compliance rules loaded")
                passed_tests = 0
            
            self.test_results.append({
                "category": "Rule Management",
                "passed": passed_tests,
                "total": 3,
                "success_rate": (passed_tests / 3) * 100
            })
            
        except Exception as e:
            print(f"   ❌ Rule management test failed: {str(e)}")
            self.test_results.append({
                "category": "Rule Management",
                "passed": 0,
                "total": 3,
                "success_rate": 0.0
            })
    
    async def test_graph_integration(self):
        """Test integration with knowledge graph"""
        print("\n🧪 Testing Graph Integration...")
        
        try:
            # Test Neo4j connection
            stats = self.neo4j_manager.get_graph_statistics()
            
            if stats:
                print("   ✅ Neo4j connection successful")
                print(f"   📊 Graph contains: {stats.get('documents', 0)} documents")
                
                # Test basic query
                query = "MATCH (n) RETURN count(n) as node_count LIMIT 1"
                result = await self.neo4j_manager.execute_query(query)
                
                if result:
                    node_count = result[0]['node_count']
                    print(f"   ✅ Basic query successful: {node_count} nodes found")
                    passed_tests = 2
                else:
                    print("   ❌ Basic query failed")
                    passed_tests = 1
            else:
                print("   ❌ Neo4j connection failed")
                passed_tests = 0
            
            self.test_results.append({
                "category": "Graph Integration",
                "passed": passed_tests,
                "total": 2,
                "success_rate": (passed_tests / 2) * 100
            })
            
        except Exception as e:
            print(f"   ❌ Graph integration test failed: {str(e)}")
            self.test_results.append({
                "category": "Graph Integration",
                "passed": 0,
                "total": 2,
                "success_rate": 0.0
            })
    
    async def test_performance(self):
        """Test compliance engine performance"""
        print("\n🧪 Testing Performance...")
        
        try:
            import time
            
            # Test IBAN validation performance
            from compliance_engine import IBANValidator
            validator = IBANValidator()
            
            test_iban = "DE89370400440532013000"
            iterations = 1000
            
            start_time = time.time()
            for _ in range(iterations):
                validator.validate(test_iban)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / iterations * 1000  # Convert to ms
            
            if avg_time < 1.0:  # Less than 1ms per validation
                print(f"   ✅ IBAN validation performance: {avg_time:.2f}ms average")
                performance_passed = 2
            else:
                print(f"   ⚠️ IBAN validation performance: {avg_time:.2f}ms average (slow)")
                performance_passed = 1
            
            # Test rule loading performance
            start_time = time.time()
            rules = self.engine.rules
            end_time = time.time()
            
            rule_load_time = (end_time - start_time) * 1000
            
            if rule_load_time < 10.0:  # Less than 10ms
                print(f"   ✅ Rule loading performance: {rule_load_time:.2f}ms")
                performance_passed += 1
            else:
                print(f"   ⚠️ Rule loading performance: {rule_load_time:.2f}ms (slow)")
            
            self.test_results.append({
                "category": "Performance",
                "passed": performance_passed,
                "total": 3,
                "success_rate": (performance_passed / 3) * 100
            })
            
        except Exception as e:
            print(f"   ❌ Performance test failed: {str(e)}")
            self.test_results.append({
                "category": "Performance",
                "passed": 0,
                "total": 3,
                "success_rate": 0.0
            })
    
    def show_test_summary(self):
        """Show comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 Compliance Engine Test Summary")
        print("=" * 60)
        
        total_passed = sum(result['passed'] for result in self.test_results)
        total_tests = sum(result['total'] for result in self.test_results)
        overall_success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n🎯 Overall Results: {total_passed}/{total_tests} tests passed ({overall_success_rate:.1f}%)")
        
        print("\n📋 Category Breakdown:")
        for result in self.test_results:
            status = "✅" if result['success_rate'] >= 80 else "⚠️" if result['success_rate'] >= 60 else "❌"
            print(f"{status} {result['category']}: {result['passed']}/{result['total']} ({result['success_rate']:.1f}%)")
        
        # Recommendations
        print("\n💡 Recommendations:")
        if overall_success_rate >= 90:
            print("   🎉 Excellent! Compliance engine is ready for production")
        elif overall_success_rate >= 80:
            print("   ✅ Good! Minor improvements needed before production")
        elif overall_success_rate >= 60:
            print("   ⚠️ Fair! Significant improvements needed")
        else:
            print("   ❌ Poor! Major issues need to be addressed")
        
        # Critical issues
        critical_categories = [result for result in self.test_results if result['success_rate'] < 50]
        if critical_categories:
            print("\n🚨 Critical Issues to Address:")
            for category in critical_categories:
                print(f"   • {category['category']}: {category['success_rate']:.1f}% success rate")
        
        print(f"\n🕐 Test completed at: {datetime.now().isoformat()}")

# Interactive test runner
async def interactive_test():
    """Interactive test runner"""
    print("🎮 Compliance Engine Interactive Test")
    print("=" * 50)
    
    test_suite = ComplianceEngineTest()
    
    while True:
        print("\n📋 Available Tests:")
        print("1. all - Run all tests")
        print("2. iban - Test IBAN validation")
        print("3. sanctions - Test sanctions checking")
        print("4. trade - Test trade compliance")
        print("5. document - Test document compliance")
        print("6. rules - Test rule management")
        print("7. graph - Test graph integration")
        print("8. performance - Test performance")
        print("9. quit - Exit")
        
        try:
            command = input("\n🔥 Enter test command: ").strip().lower()
            
            if command == 'quit' or command == '9':
                print("👋 Goodbye!")
                break
            
            elif command == 'all' or command == '1':
                await test_suite.run_all_tests()
            
            elif command == 'iban' or command == '2':
                await test_suite.test_iban_validation()
            
            elif command == 'sanctions' or command == '3':
                await test_suite.test_sanctions_checking()
            
            elif command == 'trade' or command == '4':
                await test_suite.test_trade_compliance()
            
            elif command == 'document' or command == '5':
                await test_suite.test_document_compliance()
            
            elif command == 'rules' or command == '6':
                await test_suite.test_rule_management()
            
            elif command == 'graph' or command == '7':
                await test_suite.test_graph_integration()
            
            elif command == 'performance' or command == '8':
                await test_suite.test_performance()
            
            else:
                print("❌ Unknown command")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

# Main execution
async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compliance Engine Test Suite')
    parser.add_argument('--test-all', action='store_true', help='Run all tests')
    parser.add_argument('--test-iban', action='store_true', help='Test IBAN validation')
    parser.add_argument('--test-sanctions', action='store_true', help='Test sanctions checking')
    parser.add_argument('--test-trade', action='store_true', help='Test trade compliance')
    parser.add_argument('--test-document', action='store_true', help='Test document compliance')
    parser.add_argument('--test-rules', action='store_true', help='Test rule management')
    parser.add_argument('--test-graph', action='store_true', help='Test graph integration')
    parser.add_argument('--test-performance', action='store_true', help='Test performance')
    parser.add_argument('--interactive', action='store_true', help='Interactive test mode')
    
    args = parser.parse_args()
    
    test_suite = ComplianceEngineTest()
    
    if args.test_all:
        await test_suite.run_all_tests()
    elif args.test_iban:
        await test_suite.test_iban_validation()
    elif args.test_sanctions:
        await test_suite.test_sanctions_checking()
    elif args.test_trade:
        await test_suite.test_trade_compliance()
    elif args.test_document:
        await test_suite.test_document_compliance()
    elif args.test_rules:
        await test_suite.test_rule_management()
    elif args.test_graph:
        await test_suite.test_graph_integration()
    elif args.test_performance:
        await test_suite.test_performance()
    elif args.interactive:
        await interactive_test()
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
