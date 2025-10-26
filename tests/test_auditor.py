import pytest
from app.auditor import ContractAuditor
from app.models import SeverityEnum


@pytest.fixture
def auditor():
    return ContractAuditor()


@pytest.fixture
def sample_pages():
    return [
        {"page_number": 1, "text": "Sample text", "char_start": 0, "char_end": 100}
    ]


def test_auto_renewal_short_notice(auditor, sample_pages):
    text = "This agreement will automatically renew unless you provide 15 days notice."
    extraction = {"auto_renewal": {"exists": True, "notice_period_days": 15}}

    findings = auditor.audit_contract("doc-1", text, extraction, sample_pages)

    auto_renewal_findings = [f for f in findings if f.type == "auto_renewal"]
    assert len(auto_renewal_findings) > 0
    assert auto_renewal_findings[0].severity == SeverityEnum.HIGH


def test_unlimited_liability(auditor, sample_pages):
    text = "Party shall have unlimited liability for all claims and damages."
    extraction = {}

    findings = auditor.audit_contract("doc-1", text, extraction, sample_pages)

    liability_findings = [f for f in findings if f.type == "unlimited_liability"]
    assert len(liability_findings) > 0
    assert liability_findings[0].severity == SeverityEnum.HIGH


def test_broad_indemnity(auditor, sample_pages):
    text = "Party shall indemnify against all claims, whether known or unknown."
    extraction = {"indemnity": {"exists": True, "summary": "all claims"}}

    findings = auditor.audit_contract("doc-1", text, extraction, sample_pages)

    indemnity_findings = [f for f in findings if f.type == "broad_indemnity"]
    assert len(indemnity_findings) > 0
    assert indemnity_findings[0].severity == SeverityEnum.MEDIUM


def test_missing_termination_convenience(auditor, sample_pages):
    text = "This agreement may only be terminated for cause."
    extraction = {}

    findings = auditor.audit_contract("doc-1", text, extraction, sample_pages)

    termination_findings = [f for f in findings if f.type == "missing_termination_convenience"]
    assert len(termination_findings) > 0
    assert termination_findings[0].severity == SeverityEnum.MEDIUM


def test_low_liability_cap(auditor, sample_pages):
    text = "Liability shall be limited to $10,000."
    extraction = {"liability_cap": {"amount": 10000, "currency": "USD"}}

    findings = auditor.audit_contract("doc-1", text, extraction, sample_pages)

    cap_findings = [f for f in findings if f.type == "low_liability_cap"]
    assert len(cap_findings) > 0
    assert cap_findings[0].severity == SeverityEnum.LOW


def test_no_findings_for_good_contract(auditor, sample_pages):
    text = """
    This agreement has a 60-day auto-renewal notice period.
    Liability is capped at $200,000.
    Indemnification applies only to breaches of this agreement.
    Either party may terminate for convenience with 30 days notice.
    """
    extraction = {
        "auto_renewal": {"exists": True, "notice_period_days": 60},
        "liability_cap": {"amount": 200000, "currency": "USD"},
        "indemnity": {"exists": True, "summary": "breaches only"}
    }

    findings = auditor.audit_contract("doc-1", text, extraction, sample_pages)

    high_findings = [f for f in findings if f.severity == SeverityEnum.HIGH]
    assert len(high_findings) == 0
