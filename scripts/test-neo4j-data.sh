#!/bin/bash

# Quick Test: Add Sample Data to Neo4j
echo "🧪 Adding sample data to Neo4j..."

# Add sample customer
curl -s -X POST https://kg-api-28567202440.us-central1.run.app/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Create customer Global Logistics Inc"}' \
  > /dev/null

# Add sample document
curl -s -X POST https://kg-api-28567202440.us-central1.run.app/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Create document BL12345"}' \
  > /dev/null

# Add sample location
curl -s -X POST https://kg-api-28567202440.us-central1.run.app/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Create location Port of Hamburg"}' \
  > /dev/null

echo "✅ Sample data added!"
echo ""
echo "🔍 Test queries:"
echo "1. curl -X POST https://kg-api-28567202440.us-central1.run.app/query -H \"Content-Type: application/json\" -d '{\"question\": \"Global Logistics Inc\"}'"
echo "2. curl -X POST https://kg-api-28567202440.us-central1.run.app/query -H \"Content-Type: application/json\" -d '{\"question\": \"Port of Hamburg\"}'"
echo "3. curl -X POST https://kg-api-28567202440.us-central1.run.app/query -H \"Content-Type: application/json\" -d '{\"question\": \"BL12345\"}'"
