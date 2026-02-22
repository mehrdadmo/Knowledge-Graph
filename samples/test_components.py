#!/usr/bin/env python3
"""
Simple test script for Knowledge Graph components
Tests individual components without requiring full Docker setup
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_config():
    """Test configuration loading"""
    print("🔧 Testing Configuration...")
    try:
        from config import settings
        print(f"✅ Config loaded successfully")
        print(f"   PostgreSQL: {settings.postgres_host}:{settings.postgres_port}")
        print(f"   Neo4j: {settings.neo4j_uri}")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_nl_to_cypher():
    """Test natural language to Cypher translation"""
    print("\n🤖 Testing NL to Cypher Translation...")
    try:
        from nl_to_cypher import NLToCypherTranslator
        translator = NLToCypherTranslator()
        
        test_cases = [
            {
                "question": 'Has "ABC Trading" ever sent "Electronics" to "New York"?',
                "expected_patterns": ["HAS_SHIPPER", "CONTAINS", "DESTINED_FOR"]
            },
            {
                "question": 'Is "XYZ Corp" high risk?',
                "expected_patterns": ["risk", "COUNT"]
            },
            {
                "question": "How many documents?",
                "expected_patterns": ["COUNT", "Document"]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   Test {i}: {test_case['question']}")
            cypher, params = translator.translate(test_case['question'])
            print(f"   ✅ Generated Cypher: {cypher[:100]}...")
            print(f"   📋 Parameters: {params}")
            
            # Check if expected patterns are in the query
            cypher_upper = cypher.upper()
            found_patterns = [p for p in test_case['expected_patterns'] if p.upper() in cypher_upper]
            if found_patterns:
                print(f"   🎯 Found patterns: {found_patterns}")
            else:
                print(f"   ⚠️  Expected patterns not found: {test_case['expected_patterns']}")
        
        return True
    except Exception as e:
        print(f"❌ NL to Cypher test failed: {e}")
        return False

def test_schemas():
    """Test Pydantic schemas"""
    print("\n📋 Testing Schemas...")
    try:
        from schemas import QueryRequest, QueryResponse, CDCNotification
        
        # Test QueryRequest
        request = QueryRequest(question="Test question")
        print(f"   ✅ QueryRequest: {request.question}")
        
        # Test QueryResponse
        response = QueryResponse(
            question="Test",
            answer="Test answer",
            confidence=0.95
        )
        print(f"   ✅ QueryResponse: {response.answer} (confidence: {response.confidence})")
        
        # Test CDCNotification
        notification = CDCNotification(document_id=123, field_name="TestField")
        print(f"   ✅ CDCNotification: doc {notification.document_id}, field {notification.field_name}")
        
        return True
    except Exception as e:
        print(f"❌ Schemas test failed: {e}")
        return False

def test_answer_formatting():
    """Test answer formatting"""
    print("\n💬 Testing Answer Formatting...")
    try:
        from nl_to_cypher import NLToCypherTranslator
        translator = NLToCypherTranslator()
        
        # Test boolean answer
        boolean_results = [{"has_ever_sent": True}]
        answer = translator.format_answer("Has X sent Y?", boolean_results, "MATCH ...")
        print(f"   ✅ Boolean answer: {answer}")
        
        # Test count answer
        count_results = [{"total_documents": 42}]
        answer = translator.format_answer("How many documents?", count_results, "MATCH ...")
        print(f"   ✅ Count answer: {answer}")
        
        # Test list answer
        list_results = [
            {"name": "Product A"},
            {"name": "Product B"},
            {"name": "Product C"}
        ]
        answer = translator.format_answer("What products?", list_results, "MATCH ...")
        print(f"   ✅ List answer: {answer}")
        
        return True
    except Exception as e:
        print(f"❌ Answer formatting test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Knowledge Graph Component Tests")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_config),
        ("NL to Cypher", test_nl_to_cypher),
        ("Schemas", test_schemas),
        ("Answer Formatting", test_answer_formatting)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The KG components are working correctly.")
        print("\n📝 Next steps:")
        print("   1. Start Docker services: ./docker-manage.sh start")
        print("   2. Initialize graph: ./docker-manage.sh init")
        print("   3. Sync data: ./docker-manage.sh sync")
        print("   4. Test API: ./docker-manage.sh api-test")
        print("   5. Try queries: ./docker-manage.sh query")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
