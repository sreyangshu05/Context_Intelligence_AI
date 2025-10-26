/*
  # Contract Intelligence Schema

  This migration sets up the complete database schema for the Contract Intelligence API.

  ## New Tables
  
  ### `documents`
  Stores metadata about uploaded contract PDFs
  - `id` (uuid, primary key) - unique document identifier
  - `filename` (text) - original filename
  - `mime_type` (text) - MIME type of the file
  - `file_size` (bigint) - size in bytes
  - `page_count` (integer) - number of pages
  - `upload_time` (timestamptz) - when the document was uploaded
  - `full_text` (text) - complete extracted text from all pages
  - `created_at` (timestamptz) - record creation timestamp

  ### `document_pages`
  Stores page-level text for each document
  - `id` (uuid, primary key)
  - `document_id` (uuid, foreign key) - references documents table
  - `page_number` (integer) - page number (1-indexed)
  - `text` (text) - extracted text from this page
  - `char_start` (integer) - character offset start in full document
  - `char_end` (integer) - character offset end in full document

  ### `document_chunks`
  Stores vector embeddings for RAG
  - `id` (uuid, primary key)
  - `document_id` (uuid, foreign key) - references documents table
  - `chunk_text` (text) - chunk content
  - `page_number` (integer) - page where chunk appears
  - `char_start` (integer) - character offset start
  - `char_end` (integer) - character offset end
  - `embedding` (vector(384)) - sentence embedding for similarity search

  ### `extractions`
  Stores structured field extractions
  - `id` (uuid, primary key)
  - `document_id` (uuid, foreign key, unique) - references documents table
  - `parties` (jsonb) - array of party names
  - `effective_date` (date) - contract effective date
  - `term` (text) - contract term/duration
  - `governing_law` (text) - jurisdiction
  - `payment_terms` (text) - payment description
  - `termination` (text) - termination clause summary
  - `auto_renewal` (jsonb) - {exists: bool, notice_period_days: int}
  - `confidentiality` (jsonb) - {exists: bool, summary: text}
  - `indemnity` (jsonb) - {exists: bool, summary: text}
  - `liability_cap` (jsonb) - {amount: numeric, currency: text}
  - `signatories` (jsonb) - array of {name: text, title: text}
  - `evidence` (jsonb) - field evidence spans
  - `extracted_at` (timestamptz) - extraction timestamp

  ### `audit_findings`
  Stores risk audit results
  - `id` (uuid, primary key)
  - `document_id` (uuid, foreign key) - references documents table
  - `finding_id` (text) - unique finding identifier (e.g., FIND-001)
  - `severity` (text) - HIGH, MEDIUM, or LOW
  - `type` (text) - finding type/category
  - `summary` (text) - finding description
  - `evidence` (jsonb) - array of evidence spans
  - `audited_at` (timestamptz) - audit timestamp

  ### `metrics`
  Stores API usage metrics
  - `id` (uuid, primary key)
  - `metric_name` (text) - metric identifier
  - `metric_value` (bigint) - counter value
  - `updated_at` (timestamptz) - last update timestamp

  ## Security
  
  - RLS is enabled on all tables
  - Public access policies are added for demo purposes
  - In production, these should be restricted to authenticated users
*/

-- Enable vector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  filename text NOT NULL,
  mime_type text NOT NULL DEFAULT 'application/pdf',
  file_size bigint NOT NULL,
  page_count integer NOT NULL DEFAULT 0,
  upload_time timestamptz NOT NULL DEFAULT now(),
  full_text text,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to documents"
  ON documents FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Allow public insert access to documents"
  ON documents FOR INSERT
  TO public
  WITH CHECK (true);

-- Document pages table
CREATE TABLE IF NOT EXISTS document_pages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page_number integer NOT NULL,
  text text NOT NULL,
  char_start integer NOT NULL DEFAULT 0,
  char_end integer NOT NULL DEFAULT 0,
  UNIQUE(document_id, page_number)
);

ALTER TABLE document_pages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to document_pages"
  ON document_pages FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Allow public insert access to document_pages"
  ON document_pages FOR INSERT
  TO public
  WITH CHECK (true);

-- Document chunks table for RAG
CREATE TABLE IF NOT EXISTS document_chunks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_text text NOT NULL,
  page_number integer NOT NULL,
  char_start integer NOT NULL DEFAULT 0,
  char_end integer NOT NULL DEFAULT 0,
  embedding vector(384)
);

ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to document_chunks"
  ON document_chunks FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Allow public insert access to document_chunks"
  ON document_chunks FOR INSERT
  TO public
  WITH CHECK (true);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
  ON document_chunks 
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Extractions table
CREATE TABLE IF NOT EXISTS extractions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE UNIQUE,
  parties jsonb DEFAULT '[]'::jsonb,
  effective_date date,
  term text,
  governing_law text,
  payment_terms text,
  termination text,
  auto_renewal jsonb DEFAULT '{"exists": false}'::jsonb,
  confidentiality jsonb DEFAULT '{"exists": false}'::jsonb,
  indemnity jsonb DEFAULT '{"exists": false}'::jsonb,
  liability_cap jsonb,
  signatories jsonb DEFAULT '[]'::jsonb,
  evidence jsonb DEFAULT '{}'::jsonb,
  extracted_at timestamptz DEFAULT now()
);

ALTER TABLE extractions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to extractions"
  ON extractions FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Allow public insert access to extractions"
  ON extractions FOR INSERT
  TO public
  WITH CHECK (true);

CREATE POLICY "Allow public update access to extractions"
  ON extractions FOR UPDATE
  TO public
  USING (true);

-- Audit findings table
CREATE TABLE IF NOT EXISTS audit_findings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  finding_id text NOT NULL,
  severity text NOT NULL CHECK (severity IN ('HIGH', 'MEDIUM', 'LOW')),
  type text NOT NULL,
  summary text NOT NULL,
  evidence jsonb DEFAULT '[]'::jsonb,
  audited_at timestamptz DEFAULT now()
);

ALTER TABLE audit_findings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to audit_findings"
  ON audit_findings FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Allow public insert access to audit_findings"
  ON audit_findings FOR INSERT
  TO public
  WITH CHECK (true);

CREATE POLICY "Allow public delete access to audit_findings"
  ON audit_findings FOR DELETE
  TO public
  USING (true);

-- Metrics table
CREATE TABLE IF NOT EXISTS metrics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  metric_name text NOT NULL UNIQUE,
  metric_value bigint NOT NULL DEFAULT 0,
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to metrics"
  ON metrics FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Allow public insert access to metrics"
  ON metrics FOR INSERT
  TO public
  WITH CHECK (true);

CREATE POLICY "Allow public update access to metrics"
  ON metrics FOR UPDATE
  TO public
  USING (true);

-- Initialize metrics
INSERT INTO metrics (metric_name, metric_value)
VALUES 
  ('documents_ingested', 0),
  ('extractions_performed', 0),
  ('queries_answered', 0),
  ('audits_run', 0)
ON CONFLICT (metric_name) DO NOTHING;
