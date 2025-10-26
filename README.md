# Contract Intelligence API

A production-ready REST API for contract document analysis, structured field extraction, risk assessment, and question-answering over contract corpora using RAG (Retrieval-Augmented Generation).

## Features

- **Document Ingestion**: Upload and process multiple PDF contracts with text extraction and chunking
- **Field Extraction**: Extract structured fields (parties, dates, terms, payment, liability, etc.) using rule-based + optional LLM enhancement
- **RAG Q&A**: Answer questions about uploaded contracts with source citations
- **Risk Auditing**: Automated clause risk detection (auto-renewal, unlimited liability, broad indemnity, etc.)
- **Admin Endpoints**: Health checks, metrics, and OpenAPI documentation
- **Dual Mode Operation**: Works with or without OpenAI API keys (falls back to local models)

## Technology Stack

- **Framework**: FastAPI (Python 3.11)
- **Database**: Supabase (PostgreSQL with pgvector)
- **PDF Processing**: PyMuPDF (fitz)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2) or OpenAI text-embedding-3-small
- **LLM**: OpenAI GPT-3.5-turbo (optional, with rule-based fallback)
- **Vector Search**: pgvector with cosine similarity
- **Containerization**: Docker + docker-compose

## Quick Start

### Prerequisites

- Docker and docker-compose installed
- (Optional) OpenAI API key for enhanced extraction and generation

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/sreyangshu05/Context_Intelligence_AI.git
   cd Context_Intelligence_AI
   ```

2. **Configure environment variables**

   The `.env` file is already configured with Supabase credentials. Optionally add your OpenAI API key:

   ```bash
   # .env file
   SUPABASE_URL=<already-configured>
   SUPABASE_ANON_KEY=<already-configured>

   # Optional: Add for enhanced LLM features
   OPENAI_API_KEY=sk-your-key-here

   # Audit thresholds (optional, defaults shown)
   LIABILITY_CAP_THRESHOLD=50000
   AUTO_RENEWAL_NOTICE_DAYS=30
   ```

3. **Start the application**

   ```bash
   docker-compose up --build
   ```

   The API will be available at `http://localhost:8000`

4. **Access the API documentation**

   Open your browser to `http://localhost:8000/docs` for interactive Swagger UI

### Running Without OpenAI API Key

The system is designed to work fully without OpenAI:

- **Embeddings**: Uses local sentence-transformers model (all-MiniLM-L6-v2)
- **Extraction**: Uses rule-based regex patterns and heuristics
- **RAG**: Uses keyword matching and context retrieval

Performance is good for structured contracts with standard clauses.

## API Endpoints

### 1. Ingest Documents

Upload one or more PDF contracts for processing.

```bash
curl -X POST http://localhost:8000/ingest \
  -F "files=@contract1.pdf" \
  -F "files=@contract2.pdf"
```

**Response:**
```json
{
  "documents": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "contract1.pdf",
      "pages": 12
    }
  ]
}
```

### 2. Extract Structured Fields

Extract key contract fields from an uploaded document.

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"document_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "parties": ["Acme Corp", "Beta LLC"],
  "effective_date": "2024-01-15",
  "term": "12 months",
  "governing_law": "State of California",
  "payment_terms": "5,000 monthly, Net 30",
  "termination": "30 days written notice",
  "auto_renewal": {
    "exists": true,
    "notice_period_days": 45
  },
  "confidentiality": {
    "exists": true,
    "summary": "Mutual confidentiality obligations"
  },
  "indemnity": {
    "exists": true,
    "summary": "Standard indemnification"
  },
  "liability_cap": {
    "amount": 100000,
    "currency": "INR"
  },
  "signatories": [
    {"name": "Rajiv Shukla", "title": "CEO"}
  ]
}
```

### 3. Ask Questions (RAG)

Query uploaded contracts with natural language questions.

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the effective date of the agreement?",
    "document_ids": ["550e8400-e29b-41d4-a716-446655440000"]
  }'
```

**Response:**
```json
{
  "answer": "The agreement is effective as of January 15, 2024.",
  "sources": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "page": 1,
      "char_start": 245,
      "char_end": 445,
      "excerpt": "This Agreement is entered into as of January 15, 2025..."
    }
  ]
}
```

Omit `document_ids` to search across all uploaded documents.

### 4. Audit Contract Risks

Identify risky clauses and potential issues.

```bash
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"document_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

**Response:**
```json
{
  "findings": [
    {
      "id": "FIND-001",
      "severity": "HIGH",
      "type": "auto_renewal",
      "summary": "Auto-renewal with 15 days notice (less than 30 days)",
      "evidence": [
        {
          "page": 3,
          "char_start": 1250,
          "char_end": 1450,
          "excerpt": "...automatically renew unless 15 days notice..."
        }
      ]
    },
    {
      "id": "FIND-002",
      "severity": "LOW",
      "type": "low_liability_cap",
      "summary": "Liability cap 25,000 is below recommended threshold 50,000",
      "evidence": [...]
    }
  ]
}
```

**Risk Rules:**
- **HIGH**: Auto-renewal with < 30 days notice
- **HIGH**: Unlimited or uncapped liability
- **MEDIUM**: Broad indemnity (covers "all claims")
- **MEDIUM**: Missing termination for convenience
- **LOW**: Liability cap below threshold

### 5. Health Check

```bash
curl http://localhost:8000/healthz
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 6. Metrics

```bash
curl http://localhost:8000/metrics
```

**Response:**
```json
{
  "documents_ingested": 15,
  "extractions_performed": 12,
  "queries_answered": 48,
  "audits_run": 10
}
```

### 7. API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Testing

### Run Unit Tests

```bash
docker-compose exec api pytest
```

Or locally:

```bash
pip install -r requirements.txt
pytest
```

### Run Evaluation

The evaluation script tests the RAG Q&A system against a predefined question set:

```bash
# Make sure the API is running
docker-compose up -d

# Run evaluation (requires documents to be ingested first)
python eval/run_eval.py <document_id1> <document_id2>

# Or search all documents
python eval/run_eval.py
```

Results are saved to `eval/score.txt` with a summary score and metrics.

## Sample Dataset

Public contract PDFs for testing are documented in `data/README.md`. Sources include:

- SEC EDGAR filings (NDAs, service agreements)
- Open-source project contributor agreements
- Government contract templates
- Creative Commons licensed agreements

## Architecture

### System Overview

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP/REST
┌──────▼──────────────────────────────────────┐
│           FastAPI Application               │
│  ┌────────────────────────────────────┐    │
│  │  Endpoints                          │    │
│  │  /ingest /extract /ask /audit       │    │
│  └─────────┬───────────────────────────┘    │
│            │                                 │
│  ┌─────────▼─────────┐  ┌──────────────┐   │
│  │ PDF Extractor     │  │ Field Extract│   │
│  │ (PyMuPDF)         │  │ (Regex+LLM)  │   │
│  └─────────┬─────────┘  └──────┬───────┘   │
│            │                    │            │
│  ┌─────────▼────────────────────▼───────┐   │
│  │     Embedding Service                │   │
│  │  (sentence-transformers / OpenAI)    │   │
│  └─────────┬──────────────────────────┬─┘   │
│            │                          │      │
│  ┌─────────▼────────┐    ┌───────────▼───┐  │
│  │   RAG Service    │    │   Auditor     │  │
│  │ (Vector Search)  │    │ (Risk Rules)  │  │
│  └─────────┬────────┘    └───────────┬───┘  │
└────────────┼─────────────────────────┼──────┘
             │                         │
     ┌───────▼─────────────────────────▼──────┐
     │         Supabase PostgreSQL            │
     │  ┌──────────────┐  ┌───────────────┐  │
     │  │  Documents   │  │ Vector Store  │  │
     │  │  Extractions │  │  (pgvector)   │  │
     │  │  Findings    │  │               │  │
     │  └──────────────┘  └───────────────┘  │
     └────────────────────────────────────────┘
```

### Data Model

**documents**: Core contract metadata and full text
**document_pages**: Page-level text with character offsets
**document_chunks**: Embedded text chunks for vector search
**extractions**: Structured field extractions
**audit_findings**: Risk assessment results
**metrics**: API usage counters

### Chunking Strategy

- **Chunk size**: 1000 characters
- **Overlap**: 200 characters
- **Rationale**: Balances context window with retrieval precision. Overlap ensures clauses split across chunks are still retrievable.

### Fallback Behavior

The system operates in two modes:

**With OpenAI API Key:**
- Uses text-embedding-3-small (384-dim) for embeddings
- Uses GPT-3.5-turbo for extraction enhancement and answer generation
- Higher accuracy on complex clauses

**Without OpenAI API Key (Deterministic Mode):**
- Uses sentence-transformers (all-MiniLM-L6-v2, 384-dim) for embeddings
- Uses regex-based extraction with heuristics
- Uses keyword-based answer retrieval
- Fully reproducible and works offline

### Security Considerations

- **Authentication**: Not implemented (out of scope). In production, use API keys or OAuth2.
- **Rate Limiting**: Not implemented. Recommend nginx or API Gateway rate limiting in production.
- **Input Validation**: File size limits should be added (currently unlimited).
- **RLS Policies**: Supabase tables use public access policies for demo purposes. In production, restrict to authenticated users.
- **Secret Management**: OpenAI keys in `.env`. Use secret managers (AWS Secrets Manager, HashiCorp Vault) in production.

## Trade-offs and Limitations

### Design Decisions

1. **Supabase + pgvector vs. FAISS**
   - Chose Supabase for persistence, scalability, and production-readiness
   - FAISS is faster for pure in-memory search but requires custom persistence

2. **PyMuPDF vs. pdfplumber**
   - PyMuPDF is faster and handles complex layouts better
   - pdfplumber has better table extraction (not needed here)

3. **Rule-based + LLM hybrid extraction**
   - Rules handle 80% of standard clauses reliably
   - LLM fills gaps for non-standard phrasing
   - Fallback mode ensures functionality without external APIs

4. **384-dimensional embeddings**
   - Balance between quality and speed
   - Works well for contract similarity tasks
   - Lower memory footprint than 768 or 1536-dim models

### Limitations

- **PDF Quality**: Scanned PDFs require OCR (not implemented)
- **Non-English**: Only supports English contracts
- **Complex Tables**: Extraction may miss tabular data
- **Large Files**: No streaming for very large PDFs (>100 pages may be slow)
- **Concurrent Uploads**: No locking or queue system (could cause race conditions)
- **Citation Accuracy**: Character offsets may drift with complex formatting

### Future Enhancements

- Add OCR support for scanned PDFs (Tesseract)
- Implement table extraction and parsing
- Add streaming endpoints (SSE or WebSocket)
- Add webhook support for async processing
- Support batch processing with job queue (Celery)
- Add more sophisticated NLP for clause classification
- Support multi-language contracts
- Add authentication and authorization

## LLM Prompts

All prompts are documented in the source code. See:

- `app/extractor.py`: Field extraction prompt (lines 160-175)
- `app/rag.py`: RAG answer generation prompt (lines 55-65)

Prompts are designed to be deterministic (temperature=0.1) and include explicit grounding instructions to minimize hallucinations.

## Contributing

Contributions welcome! Please ensure:

- All tests pass (`pytest`)
- Code follows PEP 8 style
- New features include tests and documentation
- Changes maintain fallback mode compatibility

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: <repository-url>/issues
- Documentation: This README and `/docs` endpoint

## Acknowledgments

- Supabase for managed PostgreSQL + pgvector
- PyMuPDF for excellent PDF processing
- sentence-transformers for local embedding models
- OpenAI for optional LLM enhancement
