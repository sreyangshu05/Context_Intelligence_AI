from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import uuid
from datetime import datetime

from app.models import (
    IngestResponse, ExtractRequest, ExtractResponse, AskRequest, AskResponse,
    AuditRequest, AuditResponse, HealthResponse, MetricsResponse, DocumentMetadata
)
from app.database import get_supabase_client, increment_metric, get_metrics
from app.pdf_extractor import PDFExtractor
from app.embeddings import embedding_service
from app.extractor import FieldExtractor
from app.auditor import ContractAuditor
from app.rag import RAGService

app = FastAPI(
    title="Contract Intelligence API",
    description="A production-ready REST API for contract analysis, extraction, and risk assessment",
    version="1.0.0"
)

pdf_extractor = PDFExtractor()
field_extractor = FieldExtractor()
auditor = ContractAuditor()
rag_service = RAGService()


@app.post("/ingest", response_model=IngestResponse, tags=["Document Management"])
async def ingest_documents(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    supabase = get_supabase_client()
    documents = []

    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")

        pdf_bytes = await file.read()

        try:
            full_text, pages_data, page_count = pdf_extractor.extract_text_from_pdf(pdf_bytes)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to extract text from {file.filename}: {str(e)}")

        document_id = str(uuid.uuid4())

        doc_data = {
            "id": document_id,
            "filename": file.filename,
            "mime_type": file.content_type or "application/pdf",
            "file_size": len(pdf_bytes),
            "page_count": page_count,
            "full_text": full_text,
            "upload_time": datetime.utcnow().isoformat()
        }

        supabase.table("documents").insert(doc_data).execute()

        for page_data in pages_data:
            page_record = {
                "document_id": document_id,
                "page_number": page_data["page_number"],
                "text": page_data["text"],
                "char_start": page_data["char_start"],
                "char_end": page_data["char_end"]
            }
            supabase.table("document_pages").insert(page_record).execute()

        chunks = pdf_extractor.chunk_text(full_text, pages_data)

        chunk_texts = [chunk["chunk_text"] for chunk in chunks]
        embeddings = embedding_service.embed_batch(chunk_texts)

        for chunk, embedding in zip(chunks, embeddings):
            chunk_record = {
                "document_id": document_id,
                "chunk_text": chunk["chunk_text"],
                "page_number": chunk["page_number"],
                "char_start": chunk["char_start"],
                "char_end": chunk["char_end"],
                "embedding": embedding
            }
            supabase.table("document_chunks").insert(chunk_record).execute()

        documents.append(DocumentMetadata(
            document_id=document_id,
            filename=file.filename,
            pages=page_count
        ))

    await increment_metric("documents_ingested")

    return IngestResponse(documents=documents)


@app.post("/extract", response_model=ExtractResponse, tags=["Analysis"])
async def extract_fields(request: ExtractRequest):
    supabase = get_supabase_client()

    doc_result = supabase.table("documents").select("*").eq("id", request.document_id).maybeSingle().execute()

    if not doc_result.data:
        raise HTTPException(status_code=404, detail="Document not found")

    pages_result = supabase.table("document_pages").select("*").eq("document_id", request.document_id).order("page_number").execute()

    full_text = doc_result.data["full_text"]
    pages_data = pages_result.data

    extraction = field_extractor.extract_fields(request.document_id, full_text, pages_data)

    extraction_record = {
        "document_id": request.document_id,
        "parties": extraction.parties,
        "effective_date": extraction.effective_date,
        "term": extraction.term,
        "governing_law": extraction.governing_law,
        "payment_terms": extraction.payment_terms,
        "termination": extraction.termination,
        "auto_renewal": extraction.auto_renewal.dict(),
        "confidentiality": extraction.confidentiality.dict(),
        "indemnity": extraction.indemnity.dict(),
        "liability_cap": extraction.liability_cap.dict() if extraction.liability_cap else None,
        "signatories": [s.dict() for s in extraction.signatories]
    }

    existing = supabase.table("extractions").select("id").eq("document_id", request.document_id).maybeSingle().execute()

    if existing.data:
        supabase.table("extractions").update(extraction_record).eq("document_id", request.document_id).execute()
    else:
        supabase.table("extractions").insert(extraction_record).execute()

    await increment_metric("extractions_performed")

    return extraction


@app.post("/ask", response_model=AskResponse, tags=["Analysis"])
async def ask_question(request: AskRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        answer, sources = rag_service.answer_question(request.question, request.document_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")

    await increment_metric("queries_answered")

    return AskResponse(answer=answer, sources=sources)


@app.post("/audit", response_model=AuditResponse, tags=["Analysis"])
async def audit_contract(request: AuditRequest):
    supabase = get_supabase_client()

    doc_result = supabase.table("documents").select("*").eq("id", request.document_id).maybeSingle().execute()

    if not doc_result.data:
        raise HTTPException(status_code=404, detail="Document not found")

    extraction_result = supabase.table("extractions").select("*").eq("document_id", request.document_id).maybeSingle().execute()

    extraction_data = extraction_result.data if extraction_result.data else {}

    pages_result = supabase.table("document_pages").select("*").eq("document_id", request.document_id).order("page_number").execute()

    full_text = doc_result.data["full_text"]
    pages_data = pages_result.data

    findings = auditor.audit_contract(request.document_id, full_text, extraction_data, pages_data)

    supabase.table("audit_findings").delete().eq("document_id", request.document_id).execute()

    for finding in findings:
        finding_record = {
            "document_id": request.document_id,
            "finding_id": finding.id,
            "severity": finding.severity.value,
            "type": finding.type,
            "summary": finding.summary,
            "evidence": finding.evidence
        }
        supabase.table("audit_findings").insert(finding_record).execute()

    await increment_metric("audits_run")

    return AuditResponse(findings=findings)


@app.get("/healthz", response_model=HealthResponse, tags=["Admin"])
async def health_check():
    return HealthResponse(status="healthy", timestamp=datetime.utcnow())


@app.get("/metrics", response_model=MetricsResponse, tags=["Admin"])
async def get_api_metrics():
    metrics = await get_metrics()
    return MetricsResponse(**metrics)


@app.get("/", tags=["Admin"])
async def root():
    return {
        "message": "Contract Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/healthz",
        "metrics": "/metrics"
    }
