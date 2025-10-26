import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.config import settings
from app.models import ExtractResponse, AutoRenewal, Confidentiality, Indemnity, LiabilityCap, Signatory


class FieldExtractor:
    def __init__(self):
        self.use_openai = bool(settings.openai_api_key)
        if self.use_openai:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            except Exception:
                self.use_openai = False

    def extract_fields(self, document_id: str, full_text: str, pages_data: List[Dict]) -> ExtractResponse:
        result = ExtractResponse(document_id=document_id)

        result.parties = self._extract_parties(full_text)
        result.effective_date = self._extract_effective_date(full_text)
        result.term = self._extract_term(full_text)
        result.governing_law = self._extract_governing_law(full_text)
        result.payment_terms = self._extract_payment_terms(full_text)
        result.termination = self._extract_termination(full_text)
        result.auto_renewal = self._extract_auto_renewal(full_text)
        result.confidentiality = self._extract_confidentiality(full_text)
        result.indemnity = self._extract_indemnity(full_text)
        result.liability_cap = self._extract_liability_cap(full_text)
        result.signatories = self._extract_signatories(full_text)

        if self.use_openai:
            result = self._enhance_with_llm(result, full_text)

        return result

    def _extract_parties(self, text: str) -> List[str]:
        parties = []

        party_patterns = [
            r'between\s+([A-Z][A-Za-z\s&.,]+?)\s+(?:and|,)',
            r'by and between\s+([A-Z][A-Za-z\s&.,]+?)(?:\s+and|\s*,)',
            r'Party\s+[A-Z]:\s*([A-Z][A-Za-z\s&.,]+)',
            r'"([A-Z][A-Za-z\s&.,]+?)"\s*\((?:hereinafter|the)\s+"(?:Company|Client|Vendor)',
        ]

        for pattern in party_patterns:
            matches = re.finditer(pattern, text[:2000], re.IGNORECASE)
            for match in matches:
                party = match.group(1).strip()
                if len(party) > 3 and party not in parties:
                    parties.append(party)

        return parties[:10]

    def _extract_effective_date(self, text: str) -> Optional[str]:
        date_patterns = [
            r'effective\s+(?:date|as\s+of)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'dated\s+(?:as\s+of\s+)?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text[:3000], re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    parsed = self._parse_date(date_str)
                    if parsed:
                        return parsed
                except:
                    pass

        return None

    def _parse_date(self, date_str: str) -> Optional[str]:
        formats = [
            "%B %d, %Y", "%B %d %Y", "%m/%d/%Y", "%Y-%m-%d",
            "%d %B %Y", "%d-%m-%Y"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except:
                continue
        return None

    def _extract_term(self, text: str) -> Optional[str]:
        term_patterns = [
            r'term[:\s]+([0-9]+\s+(?:year|month|day)s?)',
            r'duration[:\s]+([0-9]+\s+(?:year|month|day)s?)',
            r'period of\s+([0-9]+\s+(?:year|month|day)s?)',
        ]

        for pattern in term_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_governing_law(self, text: str) -> Optional[str]:
        law_patterns = [
            r'governed by the laws of\s+([A-Za-z\s,]+?)(?:\.|,|\n)',
            r'governing law[:\s]+([A-Za-z\s,]+?)(?:\.|,|\n)',
            r'jurisdiction[:\s]+([A-Za-z\s,]+?)(?:\.|,|\n)',
        ]

        for pattern in law_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_payment_terms(self, text: str) -> Optional[str]:
        payment_patterns = [
            r'payment terms?[:\s]+([^\n.]{10,100})',
            r'net\s+\d+\s+days?',
            r'\$[\d,]+(?:\.\d{2})?\s+(?:per|monthly|annually)',
        ]

        for pattern in payment_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    def _extract_termination(self, text: str) -> Optional[str]:
        term_match = re.search(r'termination[:\s]+([^\n]{20,200})', text, re.IGNORECASE)
        if term_match:
            return term_match.group(1).strip()
        return None

    def _extract_auto_renewal(self, text: str) -> AutoRenewal:
        auto_renewal_keywords = ['auto-renew', 'automatic renewal', 'automatically renew']
        exists = any(keyword in text.lower() for keyword in auto_renewal_keywords)

        notice_days = None
        if exists:
            notice_pattern = r'(\d+)\s+days?\s+(?:prior\s+)?notice'
            match = re.search(notice_pattern, text, re.IGNORECASE)
            if match:
                notice_days = int(match.group(1))

        return AutoRenewal(exists=exists, notice_period_days=notice_days)

    def _extract_confidentiality(self, text: str) -> Confidentiality:
        conf_keywords = ['confidential', 'confidentiality', 'non-disclosure']
        exists = any(keyword in text.lower() for keyword in conf_keywords)

        summary = None
        if exists:
            match = re.search(r'confidential(?:ity)?[:\s]+([^\n]{20,150})', text, re.IGNORECASE)
            if match:
                summary = match.group(1).strip()

        return Confidentiality(exists=exists, summary=summary)

    def _extract_indemnity(self, text: str) -> Indemnity:
        indem_keywords = ['indemnif', 'hold harmless']
        exists = any(keyword in text.lower() for keyword in indem_keywords)

        summary = None
        if exists:
            match = re.search(r'indemni(?:ty|fication|fy)[:\s]+([^\n]{20,150})', text, re.IGNORECASE)
            if match:
                summary = match.group(1).strip()

        return Indemnity(exists=exists, summary=summary)

    def _extract_liability_cap(self, text: str) -> Optional[LiabilityCap]:
        cap_patterns = [
            r'liability.*?(?:limited|capped|not exceed)\s+.*?\$?([\d,]+)',
            r'\$?([\d,]+).*?(?:maximum|limit).*?liability',
        ]

        for pattern in cap_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    return LiabilityCap(amount=amount, currency="USD")
                except:
                    pass

        return None

    def _extract_signatories(self, text: str) -> List[Signatory]:
        signatories = []

        sig_pattern = r'(?:By:|Signature:)\s*([A-Z][a-z]+\s+[A-Z][a-z]+)\s*(?:Title:)?\s*([A-Z][a-z\s]+)?'
        matches = re.finditer(sig_pattern, text[-2000:])

        for match in matches:
            name = match.group(1).strip() if match.group(1) else ""
            title = match.group(2).strip() if match.group(2) else ""
            signatories.append(Signatory(name=name, title=title))

        return signatories[:5]

    def _enhance_with_llm(self, result: ExtractResponse, full_text: str) -> ExtractResponse:
        try:
            prompt = f"""Extract structured information from this contract text. Return only the requested fields, use null if not found.

Contract text (first 3000 chars):
{full_text[:3000]}

Extract:
1. Parties (list of company names)
2. Effective date (YYYY-MM-DD format)
3. Term (e.g., "12 months")
4. Governing law (state/country)
5. Payment terms (brief description)

Return as JSON with keys: parties, effective_date, term, governing_law, payment_terms"""

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )

            import json
            llm_data = json.loads(response.choices[0].message.content)

            if llm_data.get("parties") and len(llm_data["parties"]) > len(result.parties):
                result.parties = llm_data["parties"]
            if llm_data.get("effective_date") and not result.effective_date:
                result.effective_date = llm_data["effective_date"]
            if llm_data.get("term") and not result.term:
                result.term = llm_data["term"]
            if llm_data.get("governing_law") and not result.governing_law:
                result.governing_law = llm_data["governing_law"]
            if llm_data.get("payment_terms") and not result.payment_terms:
                result.payment_terms = llm_data["payment_terms"]

        except Exception as e:
            print(f"LLM enhancement failed: {e}")

        return result
