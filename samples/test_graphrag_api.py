#!/usr/bin/env python3
"""
Test script for GraphRAG API endpoints
Tests natural language to Cypher query translation and API responses
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List
import time


class GraphRAGTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health(self):
        """Test health endpoint"""
        print("🏥 Testing Health Endpoint")
        print("-" * 40)
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_query(self, question: str, expected_keywords: List[str] = None) -> Dict[str, Any]:
        """Test a single query"""
        print(f"\n🤖 Question: {question}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            payload = {"question": question}
            async with self.session.post(
                f"{self.base_url}/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                data = await response.json()
                execution_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    print(f"✅ Query successful ({execution_time:.2f}ms)")
                    print(f"📝 Answer: {data.get('answer', 'No answer')}")
                    
                    if data.get('cypher_query'):
                        print(f"🔍 Cypher: {data['cypher_query']}")
                    
                    if data.get('results'):
                        print(f"📊 Results: {len(data['results'])} records")
                        # Show first result
                        if data['results']:
                            print(f"   Sample: {data['results'][0]}")
                    
                    if data.get('confidence'):
                        print(f"🎯 Confidence: {data['confidence']:.2f}")
                    
                    # Check for expected keywords
                    if expected_keywords:
                        answer_lower = data.get('answer', '').lower()
                        found_keywords = [kw for kw in expected_keywords if kw.lower() in answer_lower]
                        if found_keywords:
                            print(f"✅ Found expected keywords: {found_keywords}")
                        else:
                            print(f"⚠️  Expected keywords not found: {expected_keywords}")
                    
                    return {"success": True, "data": data, "execution_time": execution_time}
                else:
                    print(f"❌ Query failed: {response.status}")
                    print(f"Error: {data}")
                    return {"success": False, "error": data, "execution_time": execution_time}
        
        except Exception as e:
            print(f"❌ Query error: {e}")
            return {"success": False, "error": str(e), "execution_time": execution_time}
    
    async def test_stats(self):
        """Test statistics endpoint"""
        print("\n📊 Testing Statistics Endpoint")
        print("-" * 40)
        
        try:
            async with self.session.get(f"{self.base_url}/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Stats retrieved successfully")
                    
                    stats = data.get('statistics', {})
                    summary = data.get('summary', {})
                    
                    print(f"📈 Total Nodes: {summary.get('total_nodes', 0)}")
                    print(f"🔗 Total Relationships: {summary.get('total_relationships', 0)}")
                    
                    # Show node counts
                    for key, value in stats.items():
                        if key != 'relationships' and isinstance(value, int):
                            print(f"   {key.title()}: {value}")
                    
                    return True
                else:
                    print(f"❌ Stats failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Stats error: {e}")
            return False
    
    async def test_examples(self):
        """Test example queries"""
        print("\n📚 Testing Example Queries")
        print("=" * 50)
        
        try:
            async with self.session.get(f"{self.base_url}/query/examples") as response:
                if response.status == 200:
                    data = await response.json()
                    examples = data.get('examples', [])
                    print(f"✅ Retrieved {len(examples)} example queries")
                    
                    for i, example in enumerate(examples, 1):
                        print(f"\n{i}. {example.get('question', 'No question')}")
                        print(f"   {example.get('description', 'No description')}")
                    
                    return examples
                else:
                    print(f"❌ Examples failed: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Examples error: {e}")
            return []
    
    async def run_comprehensive_tests(self):
        """Run comprehensive test suite"""
        print("🧪 GraphRAG API Test Suite")
        print("=" * 60)
        
        # Test health
        health_ok = await self.test_health()
        if not health_ok:
            print("❌ Health check failed, stopping tests")
            return
        
        # Test stats
        await self.test_stats()
        
        # Get examples
        examples = await self.test_examples()
        
        # Test queries
        test_queries = [
            {
                "question": 'Has "ABC Trading Co" ever sent "Automobile parts" to "Shanghai Port"?',
                "expected_keywords": ["yes", "no", "sent", "shanghai"]
            },
            {
                "question": 'Is "XYZ Import Export" high risk?',
                "expected_keywords": ["risk", "high", "medium", "low"]
            },
            {
                "question": "What products did Global Logistics Inc send?",
                "expected_keywords": ["product", "global logistics"]
            },
            {
                "question": "How many documents are in the system?",
                "expected_keywords": ["documents", "count"]
            },
            {
                "question": "List all shippers",
                "expected_keywords": ["shipper", "legal entity"]
            },
            {
                "question": "Find documents for ABC Trading",
                "expected_keywords": ["document", "abc trading"]
            },
            {
                "question": "Which customers process the most documents?",
                "expected_keywords": ["customer", "documents"]
            }
        ]
        
        print(f"\n🎯 Testing {len(test_queries)} Queries")
        print("=" * 60)
        
        results = []
        for query_test in test_queries:
            result = await self.test_query(
                query_test["question"],
                query_test.get("expected_keywords")
            )
            results.append(result)
            
            # Small delay between queries
            await asyncio.sleep(0.5)
        
        # Summary
        print("\n📋 Test Summary")
        print("=" * 60)
        
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        
        print(f"✅ Successful: {successful}/{total}")
        print(f"❌ Failed: {total - successful}/{total}")
        
        if successful == total:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed")
        
        # Performance summary
        execution_times = [r.get("execution_time", 0) for r in results if r.get("execution_time")]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            print(f"⏱️  Average response time: {avg_time:.2f}ms")


async def main():
    """Main test function"""
    print("🚀 Starting GraphRAG API Tests")
    print("Make sure the API is running on http://localhost:8000")
    print()
    
    async with GraphRAGTester() as tester:
        await tester.run_comprehensive_tests()


if __name__ == "__main__":
    asyncio.run(main())
