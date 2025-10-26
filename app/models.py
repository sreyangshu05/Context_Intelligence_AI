from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    pages: int


class IngestResponse(BaseModel):
    documents: List[DocumentMetadata]


class ExtractRequest(BaseModel):
    document_id: str


class AutoRenewal(BaseModel):
    exists: bool
    notice_period_days: Optional[int] = None


class Confidentiality(BaseModel):
    exists: bool
    summary: Optional[str] = None


class Indemnity(BaseModel):
    exists: bool
    summary: Optional[str] = None


class LiabilityCap(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None


class Signatory(BaseModel):
    name: str = ""
    title: str = ""


class EvidenceSpan(BaseModel):
    document_id: str
    page: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    excerpt: Optional[str] = None


class ExtractResponse(BaseModel):
    document_id: str
    parties: List[str] = []
    effective_date: Optional[str] = None
    term: Optional[str] = None
    governing_law: Optional[str] = None
    payment_terms: Optional[str] = None
    termination: Optional[str] = None
    auto_renewal: AutoRenewal = Field(default_factory=lambda: AutoRenewal(exists=False))
    confidentiality: Confidentiality = Field(default_factory=lambda: Confidentiality(exists=False))
    indemnity: Indemnity = Field(default_factory=lambda: Indemnity(exists=False))
    liability_cap: Optional[LiabilityCap] = None
    signatories: List[Signatory] = []


class AskRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None


class AskResponse(BaseModel):
    answer: str
    sources: List[EvidenceSpan] = []


class SeverityEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AuditRequest(BaseModel):
    document_id: str


class AuditFinding(BaseModel):
    id: str
    severity: SeverityEnum
    type: str
    summary: str
    evidence: List[Dict[str, Any]] = []


class AuditResponse(BaseModel):
    findings: List[AuditFinding]


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime


class MetricsResponse(BaseModel):
    documents_ingested: int
    extractions_performed: int
    queries_answered: int
    audits_run: int
