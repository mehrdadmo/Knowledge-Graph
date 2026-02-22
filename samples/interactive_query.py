#!/usr/bin/env python3
"""
Interactive GraphRAG Query Client
Simple command-line interface to test the GraphRAG API
"""

import requests
import json
import sys
from typing import Dict, Any


class GraphRAGClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def query(self, question: str) -> Dict[str, Any]:
        """Send query to GraphRAG API"""
        try:
            response = requests.post(
                f"{self.base_url}/query",
                json={"question": question},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"API Error: {response.status_code}",
                    "details": response.text
                }
        
        except requests.exceptions.ConnectionError:
            return {
                "error": "Connection Error",
                "details": "Could not connect to API. Make sure it's running on localhost:8000"
            }
        except requests.exceptions.Timeout:
            return {
                "error": "Timeout",
                "details": "Request timed out after 30 seconds"
            }
        except Exception as e:
            return {
                "error": "Unexpected Error",
                "details": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        try:
            response = requests.get(f"{self.base_url}/stats", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Stats API Error: {response.status_code}"}
        except Exception as e:
            return {"error": f"Stats Error: {str(e)}"}
    
    def get_examples(self) -> Dict[str, Any]:
        """Get example queries"""
        try:
            response = requests.get(f"{self.base_url}/query/examples", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Examples API Error: {response.status_code}"}
        except Exception as e:
            return {"error": f"Examples Error: {str(e)}"}


def main():
    """Interactive CLI for testing GraphRAG"""
    client = GraphRAGClient()
    
    print("🤖 GraphRAG Interactive Query Client")
    print("=" * 50)
    print("Type 'help' for commands, 'quit' to exit")
    print()
    
    # Check if API is available
    print("🔍 Checking API availability...")
    stats = client.get_stats()
    if "error" in stats:
        print(f"❌ API not available: {stats['error']}")
        print("Make sure the API is running: docker-compose exec kg_api uvicorn api:app --host 0.0.0.0 --port 8000")
        return
    
    print("✅ API is available!")
    
    # Show current stats
    if "summary" in stats:
        summary = stats["summary"]
        print(f"📊 Graph contains {summary.get('total_nodes', 0)} nodes and {summary.get('total_relationships', 0)} relationships")
    print()
    
    while True:
        try:
            user_input = input("🤔 Ask a question (or 'help'): ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'help':
                print("\n📚 Available Commands:")
                print("  help     - Show this help")
                print("  stats    - Show graph statistics")
                print("  examples - Show example queries")
                print("  quit     - Exit the program")
                print("\n💡 Example Questions:")
                print('  Has "ABC Trading Co" ever sent "Automobile parts" to "Shanghai Port"?')
                print('  Is "XYZ Import Export" high risk?')
                print("  What products did Global Logistics Inc send?")
                print("  How many documents are in system?")
                print("  List all shippers")
                print()
                continue
            
            if user_input.lower() == 'stats':
                stats = client.get_stats()
                if "error" in stats:
                    print(f"❌ {stats['error']}")
                else:
                    print("\n📊 Graph Statistics:")
                    print(json.dumps(stats, indent=2))
                print()
                continue
            
            if user_input.lower() == 'examples':
                examples = client.get_examples()
                if "error" in examples:
                    print(f"❌ {examples['error']}")
                else:
                    print("\n📚 Example Queries:")
                    for i, example in enumerate(examples.get('examples', []), 1):
                        print(f"  {i}. {example.get('question', 'No question')}")
                        print(f"     {example.get('description', 'No description')}")
                print()
                continue
            
            # Process query
            print("\n🔄 Processing query...")
            result = client.query(user_input)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                if "details" in result:
                    print(f"   Details: {result['details']}")
            else:
                print("✅ Query successful!")
                print(f"\n📝 Answer: {result.get('answer', 'No answer')}")
                
                if result.get('cypher_query'):
                    print(f"\n🔍 Generated Cypher:")
                    print(f"   {result['cypher_query']}")
                
                if result.get('execution_time_ms'):
                    print(f"\n⏱️  Execution time: {result['execution_time_ms']:.2f}ms")
                
                if result.get('confidence'):
                    print(f"🎯 Confidence: {result['confidence']:.2f}")
                
                if result.get('results'):
                    print(f"\n📊 Results ({len(result['results'])} records):")
                    for i, record in enumerate(result['results'][:3], 1):
                        print(f"   {i}. {record}")
                    if len(result['results']) > 3:
                        print(f"   ... and {len(result['results']) - 3} more")
            
            print("\n" + "=" * 50)
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
