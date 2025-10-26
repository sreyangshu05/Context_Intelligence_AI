# Quick Start Guide

Get the Contract Intelligence API running in 5 minutes.

## 1. Start the API

```bash
docker-compose up -d
```

The API will be available at `http://localhost:8000`

## 2. Verify It's Running

```bash
curl http://localhost:8000/healthz
```

Expected response:
```json
{"status": "healthy", "timestamp": "2024-01-15T10:30:00.000Z"}
```

## 3. Upload a Contract

Create a simple test contract (save as `test_contract.txt`):

```
MASTER SERVICE AGREEMENT

This Agreement is entered into as of January 15, 2024, by and between
Acme Corporation ("Company") and Beta Services LLC ("Vendor").

TERM: This Agreement shall continue for 12 months.

PAYMENT: Vendor shall pay $5,000 per month, Net 30 days.

GOVERNING LAW: This Agreement shall be governed by the laws of California.

LIABILITY: Total liability shall not exceed $100,000.

AUTO-RENEWAL: This Agreement automatically renews for 12-month terms
unless either party provides 45 days written notice.
```

Convert to PDF (using any tool) or use this curl command with a real PDF:

```bash
curl -X POST http://localhost:8000/ingest \
  -F "files=@test_contract.pdf"
```

Save the `document_id` from the response.

## 4. Extract Fields

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"document_id": "YOUR_DOCUMENT_ID"}'
```

## 5. Ask a Question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the term of the agreement?"}'
```

## 6. Audit for Risks

```bash
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"document_id": "YOUR_DOCUMENT_ID"}'
```

## 7. Explore the Interactive Docs

Open `http://localhost:8000/docs` in your browser to:
- Try all endpoints interactively
- View request/response schemas
- Download the OpenAPI spec

## Optional: Enable OpenAI

For better accuracy, add your OpenAI key to `.env`:

```bash
OPENAI_API_KEY=sk-your-key-here
```

Restart the API:

```bash
docker-compose restart
```

## Troubleshooting

**API won't start?**
- Check logs: `docker-compose logs api`
- Verify port 8000 is available: `lsof -i :8000`

**Can't connect to Supabase?**
- Check `.env` has correct SUPABASE_URL and SUPABASE_ANON_KEY
- Verify network connectivity

**Tests failing?**
- Ensure API is running: `docker-compose up -d`
- Run tests: `npm run test` or `pytest`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Review the [design.md](design.md) for architecture details
- Check [data/README.md](data/README.md) for sample contract sources
- Run the evaluation: `python eval/run_eval.py`
