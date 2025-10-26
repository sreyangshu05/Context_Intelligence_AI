from typing import List, Optional, Dict, Any
from app.database import get_supabase_client
from app.embeddings import embedding_service
from app.config import settings


class RAGService:
    def __init__(self):
        self.use_openai = bool(settings.openai_api_key)
        if self.use_openai:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            except Exception:
                self.use_openai = False

    def answer_question(self, question: str, document_ids: Optional[List[str]] = None, top_k: int = 5) -> tuple[str, List[Dict[str, Any]]]:
        question_embedding = embedding_service.embed_text(question)

        supabase = get_supabase_client()

        if document_ids:
            result = supabase.rpc(
                "match_document_chunks",
                {
                    "query_embedding": question_embedding,
                    "match_count": top_k,
                    "filter_doc_ids": document_ids
                }
            ).execute()
        else:
            result = supabase.rpc(
                "match_document_chunks_all",
                {
                    "query_embedding": question_embedding,
                    "match_count": top_k
                }
            ).execute()

        if not result.data:
            relevant_chunks = []
            query = supabase.table("document_chunks").select("*")
            if document_ids:
                query = query.in_("document_id", document_ids)
            all_chunks = query.limit(top_k).execute()
            relevant_chunks = all_chunks.data if all_chunks.data else []
        else:
            relevant_chunks = result.data

        if not relevant_chunks:
            return "I cannot answer this question as no relevant information was found in the uploaded documents.", []

        context_text = "\n\n".join([
            f"[Document {chunk['document_id']}, Page {chunk['page_number']}]:\n{chunk['chunk_text']}"
            for chunk in relevant_chunks
        ])

        if self.use_openai:
            answer = self._generate_answer_with_llm(question, context_text)
        else:
            answer = self._generate_answer_fallback(question, context_text)

        sources = []
        for chunk in relevant_chunks:
            sources.append({
                "document_id": chunk["document_id"],
                "page": chunk["page_number"],
                "char_start": chunk["char_start"],
                "char_end": chunk["char_end"],
                "excerpt": chunk["chunk_text"][:200]
            })

        return answer, sources

    def _generate_answer_with_llm(self, question: str, context: str) -> str:
        try:
            prompt = f"""Answer the following question based ONLY on the provided context. Do not use external knowledge.
If the answer cannot be found in the context, say "I cannot answer this question based on the provided documents."

Context:
{context[:3000]}

Question: {question}

Answer:"""

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"LLM answer generation failed: {e}")
            return self._generate_answer_fallback(question, context)

    def _generate_answer_fallback(self, question: str, context: str) -> str:
        question_lower = question.lower()

        context_sentences = context.split('.')
        relevant_sentences = []

        question_keywords = set(question_lower.split()) - {'what', 'when', 'where', 'who', 'how', 'is', 'are', 'the', 'a', 'an'}

        for sentence in context_sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in question_keywords):
                relevant_sentences.append(sentence.strip())

        if relevant_sentences:
            return '. '.join(relevant_sentences[:3]) + '.'
        else:
            return context[:500] + "..."
