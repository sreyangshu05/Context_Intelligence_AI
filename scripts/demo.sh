#!/bin/bash

API_URL="http://localhost:8000"

echo "Contract Intelligence API - Demo Script"
echo "========================================"
echo ""

echo "Checking API health..."
curl -s $API_URL/healthz | python3 -m json.tool
echo ""

echo "Getting current metrics..."
curl -s $API_URL/metrics | python3 -m json.tool
echo ""

echo "========================================"
echo "Demo endpoints:"
echo ""
echo "1. Ingest a PDF:"
echo "   curl -X POST $API_URL/ingest -F 'files=@your_contract.pdf'"
echo ""
echo "2. Extract fields (replace <doc_id>):"
echo "   curl -X POST $API_URL/extract -H 'Content-Type: application/json' -d '{\"document_id\":\"<doc_id>\"}'"
echo ""
echo "3. Ask a question:"
echo "   curl -X POST $API_URL/ask -H 'Content-Type: application/json' -d '{\"question\":\"What is the effective date?\"}'"
echo ""
echo "4. Audit a contract (replace <doc_id>):"
echo "   curl -X POST $API_URL/audit -H 'Content-Type: application/json' -d '{\"document_id\":\"<doc_id>\"}'"
echo ""
echo "5. View interactive docs:"
echo "   Open http://localhost:8000/docs in your browser"
echo ""
