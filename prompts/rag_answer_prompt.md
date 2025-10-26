# RAG Answer Generation Prompt

## Purpose
Generate grounded, factual answers to user questions based solely on retrieved contract context.

## Used In
`app/rag.py` - `RAGService._generate_answer_with_llm()` method (lines 55-65)

## Prompt Template

```
Answer the following question based ONLY on the provided context. Do not use external knowledge.
If the answer cannot be found in the context, say "I cannot answer this question based on the provided documents."

Context:
{context[:3000]}

Question: {question}

Answer:
```

## Rationale

**Why this approach?**

1. **Explicit grounding**: "based ONLY on the provided context" prevents hallucination
2. **Fallback instruction**: Graceful handling when context doesn't contain answer
3. **Simple format**: No complex chain-of-thought needed for factual retrieval
4. **Context truncation**: 3000 chars balances completeness with token limits

**Temperature setting**: 0.1
- Prioritizes factual accuracy over creative phrasing
- Reduces paraphrasing that might introduce errors
- Ensures consistent answers across identical questions

**Context structure**:
```
[Document UUID, Page N]:
<chunk text>

[Document UUID, Page M]:
<chunk text>
...
```
- Clear document/page attribution for traceability
- Allows model to reference specific sources
- Supports multi-document queries

## Example Input/Output

**Input:**
```
Context:
[Document 550e8400-e29b-41d4-a716-446655440000, Page 1]:
This Agreement is effective as of January 15, 2024 between Acme Corp and Beta LLC.

[Document 550e8400-e29b-41d4-a716-446655440000, Page 2]:
The term of this Agreement shall be twelve (12) months from the Effective Date.

Question: What is the term of the agreement?
```

**Output:**
```
The term of the Agreement is twelve (12) months from the Effective Date.
```

## Anti-Hallucination Strategies

1. **Explicit constraints**: "based ONLY on the provided context"
2. **Fallback instruction**: "If the answer cannot be found..."
3. **Low temperature**: 0.1 (deterministic, factual)
4. **Context attribution**: Document IDs help model ground responses
5. **Limited context**: 3000 chars prevents overwhelming the model

## Failure Modes

**Case 1: Context doesn't contain answer**
- Expected output: "I cannot answer this question based on the provided documents."
- Model behavior: Generally complies due to explicit instruction

**Case 2: Ambiguous question**
- Model may provide partial answer or request clarification
- Acceptable: reflects genuinely unclear user intent

**Case 3: Conflicting information**
- Model should surface the conflict or provide both perspectives
- Future improvement: explicit conflict detection prompt

## Alternatives Considered

1. **Chain-of-thought prompting**: More accurate but slower and verbose
2. **Few-shot examples**: Marginal improvement, not worth token cost
3. **Structured output (JSON)**: Over-engineered for simple Q&A
4. **Multi-step reasoning**: Overkill for factual retrieval

## Token Budget

- Prompt: ~100 tokens
- Context: ~750 tokens (3000 chars ≈ 750 tokens)
- Question: ~20 tokens
- Answer: ~100 tokens (max_tokens=300)
- **Total**: ~970 tokens per query

Cost-effective for gpt-3.5-turbo ($0.001/1K tokens).

## Evaluation Metrics

- **Faithfulness**: Answer must be in context (checked manually)
- **Relevance**: Answer must address the question
- **Conciseness**: Prefer shorter, direct answers
- **Citation**: Sources returned separately by RAG service

## Fallback Mode (No LLM)

When OpenAI is unavailable, the system uses keyword-based extraction:

1. Extract keywords from question (remove stopwords)
2. Find sentences in context containing keywords
3. Return top 3 matching sentences
4. Less fluent but factually grounded

This ensures system functionality without external dependencies.
