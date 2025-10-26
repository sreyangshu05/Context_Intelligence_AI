import re
from typing import List, Dict, Any
from app.config import settings
from app.models import AuditFinding, SeverityEnum


class ContractAuditor:
    def __init__(self):
        self.liability_threshold = settings.liability_cap_threshold
        self.renewal_notice_threshold = settings.auto_renewal_notice_days

    def audit_contract(self, document_id: str, full_text: str, extraction_data: Dict[str, Any], pages_data: List[Dict]) -> List[AuditFinding]:
        findings = []

        findings.extend(self._check_auto_renewal(document_id, full_text, extraction_data, pages_data))
        findings.extend(self._check_unlimited_liability(document_id, full_text, extraction_data, pages_data))
        findings.extend(self._check_broad_indemnity(document_id, full_text, extraction_data, pages_data))
        findings.extend(self._check_termination_convenience(document_id, full_text, pages_data))
        findings.extend(self._check_liability_cap(document_id, full_text, extraction_data, pages_data))

        return findings

    def _check_auto_renewal(self, document_id: str, full_text: str, extraction_data: Dict, pages_data: List[Dict]) -> List[AuditFinding]:
        findings = []

        auto_renewal = extraction_data.get("auto_renewal", {})
        if isinstance(auto_renewal, dict) and auto_renewal.get("exists"):
            notice_days = auto_renewal.get("notice_period_days")

            if notice_days and notice_days < self.renewal_notice_threshold:
                evidence = self._find_evidence(full_text, pages_data, ["auto-renew", "automatic renewal"])

                findings.append(AuditFinding(
                    id=f"FIND-{len(findings)+1:03d}",
                    severity=SeverityEnum.HIGH,
                    type="auto_renewal",
                    summary=f"Auto-renewal with {notice_days} days notice (less than {self.renewal_notice_threshold} days)",
                    evidence=evidence
                ))
            elif not notice_days:
                evidence = self._find_evidence(full_text, pages_data, ["auto-renew", "automatic renewal"])

                findings.append(AuditFinding(
                    id=f"FIND-{len(findings)+1:03d}",
                    severity=SeverityEnum.HIGH,
                    type="auto_renewal",
                    summary="Auto-renewal clause with unclear notice period",
                    evidence=evidence
                ))

        return findings

    def _check_unlimited_liability(self, document_id: str, full_text: str, extraction_data: Dict, pages_data: List[Dict]) -> List[AuditFinding]:
        findings = []

        liability_cap = extraction_data.get("liability_cap")

        unlimited_patterns = [
            r'unlimited\s+liability',
            r'liability.*without\s+limit',
            r'no\s+limitation\s+on\s+liability'
        ]

        for pattern in unlimited_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                evidence = self._find_evidence(full_text, pages_data, ["unlimited liability", "without limit"])

                findings.append(AuditFinding(
                    id=f"FIND-{len(findings)+1:03d}",
                    severity=SeverityEnum.HIGH,
                    type="unlimited_liability",
                    summary="Contract contains unlimited liability clause",
                    evidence=evidence
                ))
                break

        if not liability_cap and not findings:
            if re.search(r'liability', full_text, re.IGNORECASE):
                evidence = self._find_evidence(full_text, pages_data, ["liability"])[:1]

                findings.append(AuditFinding(
                    id=f"FIND-{len(findings)+1:03d}",
                    severity=SeverityEnum.HIGH,
                    type="unlimited_liability",
                    summary="No liability cap specified in contract",
                    evidence=evidence
                ))

        return findings

    def _check_broad_indemnity(self, document_id: str, full_text: str, extraction_data: Dict, pages_data: List[Dict]) -> List[AuditFinding]:
        findings = []

        indemnity = extraction_data.get("indemnity", {})
        if isinstance(indemnity, dict) and indemnity.get("exists"):
            broad_patterns = [
                r'indemnif(?:y|ication).*all\s+claims',
                r'indemnif(?:y|ication).*any\s+and\s+all',
                r'hold\s+harmless.*all\s+claims'
            ]

            for pattern in broad_patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    evidence = self._find_evidence(full_text, pages_data, ["indemnif", "hold harmless"])

                    findings.append(AuditFinding(
                        id=f"FIND-{len(findings)+1:03d}",
                        severity=SeverityEnum.MEDIUM,
                        type="broad_indemnity",
                        summary="Indemnity clause covers broad scope (all claims)",
                        evidence=evidence
                    ))
                    break

        return findings

    def _check_termination_convenience(self, document_id: str, full_text: str, pages_data: List[Dict]) -> List[AuditFinding]:
        findings = []

        convenience_patterns = [
            r'terminat(?:e|ion).*for\s+convenience',
            r'terminat(?:e|ion).*without\s+cause',
            r'either\s+party\s+may\s+terminat(?:e|ion)'
        ]

        has_convenience = any(re.search(pattern, full_text, re.IGNORECASE) for pattern in convenience_patterns)

        if not has_convenience:
            evidence = self._find_evidence(full_text, pages_data, ["terminat"])[:1]

            findings.append(AuditFinding(
                id=f"FIND-{len(findings)+1:03d}",
                severity=SeverityEnum.MEDIUM,
                type="missing_termination_convenience",
                summary="Contract lacks termination for convenience clause",
                evidence=evidence
            ))

        return findings

    def _check_liability_cap(self, document_id: str, full_text: str, extraction_data: Dict, pages_data: List[Dict]) -> List[AuditFinding]:
        findings = []

        liability_cap = extraction_data.get("liability_cap")

        if liability_cap and isinstance(liability_cap, dict):
            amount = liability_cap.get("amount")
            if amount and amount < self.liability_threshold:
                evidence = self._find_evidence(full_text, pages_data, ["liability", "limit"])

                findings.append(AuditFinding(
                    id=f"FIND-{len(findings)+1:03d}",
                    severity=SeverityEnum.LOW,
                    type="low_liability_cap",
                    summary=f"Liability cap ${amount:,.0f} is below recommended threshold ${self.liability_threshold:,.0f}",
                    evidence=evidence
                ))

        return findings

    def _find_evidence(self, full_text: str, pages_data: List[Dict], keywords: List[str]) -> List[Dict[str, Any]]:
        evidence = []

        for keyword in keywords:
            pattern = re.compile(f'.{{0,100}}{re.escape(keyword)}.{{0,100}}', re.IGNORECASE)
            matches = list(pattern.finditer(full_text))

            for match in matches[:2]:
                char_start = match.start()
                char_end = match.end()

                page_num = 1
                for page_data in pages_data:
                    if page_data["char_start"] <= char_start < page_data["char_end"]:
                        page_num = page_data["page_number"]
                        break

                evidence.append({
                    "page": page_num,
                    "char_start": char_start,
                    "char_end": char_end,
                    "excerpt": match.group(0)
                })

            if evidence:
                break

        return evidence[:3]
