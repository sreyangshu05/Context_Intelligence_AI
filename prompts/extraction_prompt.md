# Field Extraction Prompt

## Purpose
Enhance rule-based extraction with LLM-based refinement for ambiguous or non-standard contract fields.

## Used In
`app/extractor.py` - `FieldExtractor._enhance_with_llm()` method (lines 160-175)

## Prompt Template

```
Extract structured information from this contract text. Return only the requested fields, use null if not found.

Contract text (first 3000 chars):
{full_text[:3000]}

Extract:
1. Parties (list of company names)
2. Effective date (YYYY-MM-DD format)
3. Term (e.g., "12 months")
4. Governing law (state/country)
5. Payment terms (brief description)

Return as JSON with keys: parties, effective_date, term, governing_law, payment_terms
```

## Rationale

**Why this approach?**

1. **Limited context**: First 3000 chars capture most header/intro sections where key fields appear
2. **Explicit format**: Reduces LLM hallucination by specifying exact output format
3. **Selective enhancement**: Only queries LLM for fields where rule-based extraction failed
4. **JSON output**: Structured response is easy to parse and validate

**Temperature setting**: 0.1
- Low temperature ensures deterministic, factual extraction
- Reduces creative interpretation of ambiguous clauses
- Maintains consistency across re-runs

**Field selection**:
- Focuses on high-value, high-ambiguity fields
- Rule-based extraction handles most cases; LLM fills gaps
- Avoids querying LLM for easily regex-matched fields (e.g., dates in standard formats)

## Example Input/Output

**Input:**
```
MASTER SERVICE AGREEMENT

This Agreement is made as of March 1, 2024 between TechCorp Inc.
and DataServices LLC. The term shall be eighteen months...
```

**Output:**
```json
{
  "parties": ["TechCorp Inc.", "DataServices LLC"],
  "effective_date": "2024-03-01",
  "term": "18 months",
  "governing_law": null,
  "payment_terms": null
}
```

## Limitations

- Only processes first 3000 characters (may miss late-appearing fields)
- Relies on LLM's understanding of legal terminology
- May produce null for valid but non-standard phrasings
- No explicit citation/evidence extraction (handled separately)

## Alternatives Considered

1. **Full-text processing**: Too expensive, exceeds context window
2. **Multi-step prompting**: More accurate but slower (3-5x API calls)
3. **Zero-shot vs. few-shot**: Zero-shot sufficient for standard contracts
