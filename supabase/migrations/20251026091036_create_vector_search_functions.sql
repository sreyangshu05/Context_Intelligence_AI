/*
  # Vector Search Functions

  Creates PostgreSQL functions for vector similarity search used by the RAG system.

  ## Functions

  ### `match_document_chunks`
  Searches for similar document chunks filtered by specific document IDs
  - Parameters:
    - `query_embedding` (vector) - the query embedding to match against
    - `match_count` (int) - number of results to return
    - `filter_doc_ids` (uuid[]) - array of document IDs to filter by
  - Returns: chunks ordered by similarity

  ### `match_document_chunks_all`
  Searches for similar document chunks across all documents
  - Parameters:
    - `query_embedding` (vector) - the query embedding to match against
    - `match_count` (int) - number of results to return
  - Returns: chunks ordered by similarity
*/

-- Function to match chunks with document ID filter
CREATE OR REPLACE FUNCTION match_document_chunks(
  query_embedding vector(384),
  match_count int DEFAULT 5,
  filter_doc_ids uuid[] DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  document_id uuid,
  chunk_text text,
  page_number int,
  char_start int,
  char_end int,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    document_chunks.id,
    document_chunks.document_id,
    document_chunks.chunk_text,
    document_chunks.page_number,
    document_chunks.char_start,
    document_chunks.char_end,
    1 - (document_chunks.embedding <=> query_embedding) as similarity
  FROM document_chunks
  WHERE filter_doc_ids IS NULL OR document_chunks.document_id = ANY(filter_doc_ids)
  ORDER BY document_chunks.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Function to match chunks across all documents
CREATE OR REPLACE FUNCTION match_document_chunks_all(
  query_embedding vector(384),
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  document_id uuid,
  chunk_text text,
  page_number int,
  char_start int,
  char_end int,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    document_chunks.id,
    document_chunks.document_id,
    document_chunks.chunk_text,
    document_chunks.page_number,
    document_chunks.char_start,
    document_chunks.char_end,
    1 - (document_chunks.embedding <=> query_embedding) as similarity
  FROM document_chunks
  ORDER BY document_chunks.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
