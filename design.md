# Contract Intelligence API - Design Document

## 1. Architecture Overview

### High-Level Architecture

The system follows a modern microservices-inspired architecture with clear separation of concerns:

```
┌──────────────────────────────────────────────────────────────┐
│                      Client Layer                             │
│              (HTTP/REST, curl, Python, etc.)                  │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                   API Gateway Layer                           │
│                    (FastAPI Router)                           │
│  ┌─────────┬─────────┬─────────┬────────┬────────────────┐  │
│  │ /ingest │/extract │  /ask   │ /audit │ /healthz, etc  │  │
│  └────┬────┴────┬────┴────┬────┴───┬────┴────────┬───────┘  │
└───────┼─────────┼──────────┼────────┼─────────────┼──────────┘
        │         │          │        │             │
        ▼         ▼          ▼        ▼             ▼
┌──────────────────────────────────────────────────────────────┐
│                    Service Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐ │
│  │   PDF    │  │  Field   │  │   RAG   │  │   Auditor    │ │
│  │Extractor │  │Extractor │  │ Service │  │   Service    │ │
│  └────┬─────┘  └────┬─────┘  └────┬────┘  └──────┬───────┘ │
│       │             │              │               │          │
│       └─────────────┴──────────────┴───────────────┘          │
│                          │                                     │
│                          ▼                                     │
│              ┌───────────────────────┐                        │
│              │  Embedding Service    │                        │
│              │  (Local / OpenAI)     │                        │
│              └───────────┬───────────┘                        │
└──────────────────────────┼────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   Data Layer                                  │
│              (Supabase PostgreSQL)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  documents   │  │document_chunks│  │ extractions  │       │
│  │document_pages│  │ (w/ vectors) │  │audit_findings│       │
│  │   metrics    │  │              │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                         (pgvector)                            │
└──────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**API Layer (main.py)**
- HTTP request handling and routing
- Request validation (Pydantic models)
- Response serialization
- Error handling and status codes
- OpenAPI documentation generation

**PDF Extractor Service**
- Binary PDF parsing (PyMuPDF)
- Text extraction per page
- Character offset tracking
- Text chunking with overlap
- Handles corrupt/malformed PDFs

**Field Extractor Service**
- Rule-based pattern matching (regex)
- Date parsing and normalization
- Entity recognition (parties, signatories)
- Optional LLM enhancement
- Evidence span tracking

**RAG Service**
- Query embedding generation
- Vector similarity search
- Context retrieval and ranking
- Answer generation (LLM or fallback)
- Source citation extraction

**Auditor Service**
- Risk rule engine
- Clause pattern detection
- Severity classification
- Evidence collection
- Configurable thresholds

**Embedding Service**
- Model selection (local vs. API)
- Batch embedding generation
- Fallback handling
- Dimension consistency (384-dim)

**Database Layer**
- CRUD operations via Supabase client
- Vector similarity functions (RPC)
- Transaction management
- Metrics tracking

## 2. Data Model

### Entity-Relationship Diagram

```
documents (1) ──────< (N) document_pages
    │
    │ (1)
    │
    ├───────< (N) document_chunks [vector embeddings]
    │
    │ (1)
    │
    ├───────< (1) extractions
    │
    │ (1)
    │
    └───────< (N) audit_findings

metrics (standalone)
```

### Table Schemas

**documents**
- Primary entity storing uploaded contracts
- `full_text`: Complete document text for search
- `page_count`: Used for pagination and progress
- Indexed on `id` (primary key, UUID)

**document_pages**
- Page-level text with boundaries
- `char_start`, `char_end`: Global character offsets
- Enables precise citation extraction
- Indexed on `(document_id, page_number)`

**document_chunks**
- Fixed-size text chunks for vector search
- `embedding`: 384-dimensional vector (pgvector)
- IVFFlat index for fast cosine similarity
- 200-character overlap prevents clause splitting

**extractions**
- One-to-one with documents
- JSONB fields for flexible nested structures
- `evidence` stores field provenance
- UPSERT semantics (re-extraction updates)

**audit_findings**
- Many findings per document
- Severity enum: HIGH | MEDIUM | LOW
- Cascading delete with document
- Time-series data (audited_at)

**metrics**
- Simple counters for monitoring
- Atomic increments (no race conditions)
- Could be extended to time-series

### Why Supabase + pgvector?

**Advantages:**
- Native vector similarity search (no separate vector DB)
- ACID transactions for data integrity
- Rich query capabilities (joins, aggregations)
- Built-in connection pooling and scaling
- RESTful API and real-time subscriptions

**Trade-offs:**
- Slightly slower than pure FAISS for massive datasets
- Vector index build time increases with data size
- Requires PostgreSQL 14+ with pgvector extension

## 3. Chunking Rationale

### Strategy

- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters (20%)
- **Boundary**: Character-based (not token-based)

### Reasoning

**Why 1000 characters?**
- Typical contract clause length: 200-800 characters
- Ensures most clauses fit within a single chunk
- Balances embedding quality vs. retrieval precision
- ~150-200 tokens (within model context windows)

**Why 200-character overlap?**
- Prevents clause splitting at chunk boundaries
- Increases recall for clauses near edges
- 20% overlap is standard in RAG systems
- Trade-off: 20% storage overhead for better retrieval

**Character vs. Token Chunking**
- Characters are deterministic and language-agnostic
- Tokens require tokenizer dependency (complexity)
- Slight loss in semantic coherence (acceptable for legal text)

### Alternative Approaches Considered

1. **Sentence-based chunking**: Too variable (sentences range 10-500 words)
2. **Paragraph-based chunking**: Inconsistent in legal documents
3. **Clause-based chunking**: Requires clause detection (complex, error-prone)
4. **Fixed token chunking**: Adds tokenizer dependency, same results

## 4. Fallback Behavior

### Dual Mode Architecture

The system operates in two modes based on `OPENAI_API_KEY` presence:

#### Mode 1: Enhanced (with OpenAI)

**Embeddings**:
- OpenAI text-embedding-3-small (384-dim)
- Batch API for efficiency
- Fallback to local on rate limit

**Extraction**:
- Rule-based for structured fields
- LLM refinement for ambiguous cases
- Prompt engineering for grounding

**RAG**:
- GPT-3.5-turbo for answer generation
- Temperature 0.1 (deterministic)
- Explicit "no hallucination" instructions

**Pros**: Higher accuracy, better phrasing, handles edge cases
**Cons**: API costs, latency, rate limits, external dependency

#### Mode 2: Deterministic (without OpenAI)

**Embeddings**:
- sentence-transformers (all-MiniLM-L6-v2)
- Local inference (CPU or GPU)
- Cached model weights

**Extraction**:
- Pure regex and heuristics
- Date parsing with multiple formats
- Pattern matching for common clauses

**RAG**:
- Keyword-based answer extraction
- Sentence relevance scoring
- Context window assembly

**Pros**: No API costs, offline operation, reproducible, fast
**Cons**: Lower accuracy on non-standard clauses, simpler answers

### Fallback Logic

```python
if settings.openai_api_key:
    try:
        result = call_openai_api()
    except Exception:
        result = fallback_method()
else:
    result = fallback_method()
```

All services implement graceful degradation with logging.

## 5. Security Considerations

### Authentication & Authorization

**Current State**: None (demo/prototype)

**Production Recommendations**:
- API key authentication (header-based)
- OAuth2 / JWT for user-based access
- Rate limiting per user/key (Redis-backed)
- CORS configuration for web clients

### Input Validation

**Implemented**:
- Pydantic models for type safety
- File extension validation (.pdf only)
- Non-empty question validation

**Recommended Additions**:
- File size limits (e.g., 50MB per PDF)
- Total upload quota per user
- Malicious PDF detection (sanitization)
- SQL injection prevention (Supabase handles this)

### Data Privacy

**Considerations**:
- Uploaded contracts may contain PII/confidential data
- No encryption at rest (Supabase default)
- No data retention policies

**Production Requirements**:
- Encrypt sensitive fields (AES-256)
- Implement data retention policies (auto-delete after N days)
- Audit logging for data access
- GDPR compliance (right to deletion)

### Row-Level Security (RLS)

**Current State**: Public access policies for demo

**Production Configuration**:
```sql
-- Restrict to authenticated users
CREATE POLICY "authenticated_only"
  ON documents FOR ALL
  TO authenticated
  USING (auth.uid() IS NOT NULL);

-- User owns their documents
CREATE POLICY "user_documents"
  ON documents FOR ALL
  TO authenticated
  USING (user_id = auth.uid());
```

### Secret Management

**Current**: `.env` file (not suitable for production)

**Recommendations**:
- AWS Secrets Manager / Azure Key Vault
- Environment variable injection (K8s secrets)
- Rotate API keys regularly
- Never log secrets

### Rate Limiting

**Current**: None

**Recommended**:
- nginx rate limiting (10 req/sec per IP)
- Application-level rate limiting (slowapi)
- OpenAI rate limit handling (backoff + retry)

### Network Security

- **TLS/HTTPS**: Required in production
- **VPC**: Isolate database in private network
- **Firewall**: Whitelist API IPs for database access

## 6. Performance Considerations

### Bottlenecks

1. **PDF Extraction**: CPU-bound, scales linearly with page count
2. **Embedding Generation**: GPU acceleration helps, batching essential
3. **Vector Search**: Index size affects query time (IVFFlat)
4. **LLM Calls**: Network latency, rate limits

### Optimization Strategies

**Caching**:
- Cache extracted text (done: database)
- Cache embeddings (done: database)
- Cache LLM responses (not implemented, consider Redis)

**Parallelization**:
- Batch embed chunks (implemented)
- Async API calls (FastAPI handles this)
- Multi-file ingestion (could parallelize per-file)

**Database**:
- Index tuning (IVFFlat lists parameter)
- Connection pooling (Supabase default)
- Partial indexes for common queries

**Scaling**:
- Horizontal: Multiple API instances (stateless)
- Vertical: GPU for embeddings, more CPU for PDF
- Queue system: Celery + Redis for async processing

### Load Testing Results (Expected)

- **Ingestion**: ~5 pages/sec (CPU-bound)
- **Extraction**: ~1 doc/sec (with LLM calls)
- **RAG**: ~500ms per query (vector search + LLM)
- **Audit**: ~200ms per doc (rule-based)

## 7. Deployment

### Docker Architecture

- **Single container**: API + dependencies
- **External DB**: Supabase (managed)
- **Volumes**: None required (stateless)
- **Restart policy**: always (production)

### Environment Variables

Required:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

Optional:
- `OPENAI_API_KEY`
- `LIABILITY_CAP_THRESHOLD`
- `AUTO_RENEWAL_NOTICE_DAYS`

### Health Checks

- Endpoint: `/healthz`
- Interval: 30s
- Timeout: 5s
- Unhealthy threshold: 3 failures

### Logging

- **Level**: INFO (production), DEBUG (dev)
- **Format**: JSON structured logs
- **Output**: stdout (captured by Docker/K8s)
- **Monitoring**: Integrate with Datadog/Splunk/ELK

### Monitoring

**Key Metrics**:
- Request rate (req/sec)
- Latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database connection pool usage
- Embedding generation time

**Alerts**:
- Error rate > 5%
- Latency p95 > 2s
- Database connection pool > 80%

## 8. Future Enhancements

### Short-term (1-3 months)

1. **Streaming Endpoints**: SSE for real-time answers
2. **Webhook Support**: Async processing notifications
3. **Batch API**: Process multiple documents in one request
4. **OCR Support**: Handle scanned PDFs (Tesseract)

### Medium-term (3-6 months)

5. **Table Extraction**: Detect and parse tables (Camelot/Tabula)
6. **Multi-language**: Support non-English contracts (mBERT)
7. **Advanced NLP**: Clause classification, entity linking
8. **UI Dashboard**: Web interface for non-technical users

### Long-term (6-12 months)

9. **Fine-tuned Models**: Contract-specific embeddings
10. **Graph Database**: Model contract relationships
11. **Comparative Analysis**: Compare multiple contracts
12. **Risk Scoring**: ML-based risk prediction

## 9. Testing Strategy

### Unit Tests

- Service-level functions (extractor, auditor, RAG)
- Mocked external dependencies (OpenAI, Supabase)
- Edge cases (empty docs, malformed PDFs)

### Integration Tests

- Full API endpoint testing
- Database operations (real Supabase instance)
- End-to-end workflows (ingest → extract → ask → audit)

### Evaluation

- QA pair evaluation (F1 score, exact match)
- Extraction accuracy (field-by-field precision/recall)
- Audit coverage (detection rate for known risks)

### Performance Tests

- Load testing (locust, k6)
- Stress testing (find breaking point)
- Latency benchmarks

## 10. Conclusion

This design balances:
- **Production-readiness**: Docker, Supabase, health checks
- **Flexibility**: Dual-mode operation (with/without OpenAI)
- **Maintainability**: Clear separation of concerns, typed APIs
- **Performance**: Batch processing, vector indexing
- **Extensibility**: Modular services, plugin architecture

Key strengths:
- Works offline (no external API required)
- Scales horizontally (stateless API)
- Comprehensive error handling
- Rich documentation and testing

Areas for improvement:
- Authentication and authorization
- Advanced security (encryption, RLS)
- Production monitoring and alerting
- More sophisticated NLP (fine-tuned models)
