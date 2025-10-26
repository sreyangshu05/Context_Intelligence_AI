import pytest
from app.extractor import FieldExtractor


@pytest.fixture
def extractor():
    return FieldExtractor()


@pytest.fixture
def sample_contract():
    return """
    MASTER SERVICE AGREEMENT

    This Agreement is entered into as of January 15, 2024, by and between
    Acme Corporation ("Company") and Beta Services LLC ("Vendor").

    1. TERM
    This Agreement shall commence on the Effective Date and continue for a period
    of 12 months, unless earlier terminated in accordance with the terms herein.

    2. PAYMENT TERMS
    Client shall pay Vendor $5,000 per month, due within Net 30 days of invoice.

    3. GOVERNING LAW
    This Agreement shall be governed by the laws of the State of California.

    4. LIABILITY
    In no event shall either party's liability exceed $100,000.

    5. CONFIDENTIALITY
    Each party agrees to maintain the confidentiality of all proprietary information
    disclosed by the other party during the term of this Agreement.

    6. INDEMNIFICATION
    Each party shall indemnify and hold harmless the other party from any claims
    arising out of its negligent acts or omissions.

    7. TERMINATION
    Either party may terminate this Agreement for convenience upon 30 days written notice.

    8. AUTO-RENEWAL
    This Agreement shall automatically renew for successive 12-month terms unless
    either party provides written notice of non-renewal at least 45 days prior to
    the end of the then-current term.
    """


def test_extract_parties(extractor, sample_contract):
    result = extractor.extract_fields("test-doc-1", sample_contract, [])
    assert len(result.parties) > 0
    assert any("Acme" in party or "Beta" in party for party in result.parties)


def test_extract_effective_date(extractor, sample_contract):
    result = extractor.extract_fields("test-doc-1", sample_contract, [])
    assert result.effective_date is not None
    assert "2024" in result.effective_date


def test_extract_term(extractor, sample_contract):
    result = extractor.extract_fields("test-doc-1", sample_contract, [])
    assert result.term is not None
    assert "12" in result.term or "month" in result.term.lower()


def test_extract_governing_law(extractor, sample_contract):
    result = extractor.extract_fields("test-doc-1", sample_contract, [])
    assert result.governing_law is not None
    assert "California" in result.governing_law


def test_extract_payment_terms(extractor, sample_contract):
    result = extractor.extract_fields("test-doc-1", sample_contract, [])
    assert result.payment_terms is not None
    assert "5,000" in result.payment_terms or "Net 30" in result.payment_terms


def test_extract_auto_renewal(extractor, sample_contract):
    result = extractor.extract_fields("test-doc-1", sample_contract, [])
    assert result.auto_renewal.exists is True
    assert result.auto_renewal.notice_period_days == 45


def test_extract_confidentiality(extractor, sample_contract):
    result = extractor.extract_fields("test-doc-1", sample_contract, [])
    assert result.confidentiality.exists is True


def test_extract_indemnity(extractor, sample_contract):
    result = extractor.extract_fields("test-doc-1", sample_contract, [])
    assert result.indemnity.exists is True


def test_extract_liability_cap(extractor, sample_contract):
    result = extractor.extract_fields("test-doc-1", sample_contract, [])
    assert result.liability_cap is not None
    assert result.liability_cap.amount == 100000.0
