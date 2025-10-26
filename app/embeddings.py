from typing import List, Optional
import numpy as np
from app.config import settings


class EmbeddingService:
    def __init__(self):
        self.use_openai = bool(settings.openai_api_key)
        self.model = None

        if self.use_openai:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            except Exception as e:
                print(f"Failed to initialize OpenAI: {e}. Falling back to sentence-transformers.")
                self.use_openai = False

        if not self.use_openai:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def embed_text(self, text: str) -> List[float]:
        if self.use_openai:
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text,
                    dimensions=384
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"OpenAI embedding failed: {e}. Using fallback.")
                if not self.model:
                    from sentence_transformers import SentenceTransformer
                    self.model = SentenceTransformer('all-MiniLM-L6-v2')

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if self.use_openai:
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=texts,
                    dimensions=384
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                print(f"OpenAI batch embedding failed: {e}. Using fallback.")
                if not self.model:
                    from sentence_transformers import SentenceTransformer
                    self.model = SentenceTransformer('all-MiniLM-L6-v2')

        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


embedding_service = EmbeddingService()
