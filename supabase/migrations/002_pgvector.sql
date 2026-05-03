-- pgvector schema for the RAG documents table.
--
-- The vector dimension MUST match the embedding model in
-- packages/rag/agentos_rag/embeddings.py. AgentOS only promotes the
-- options that work on a free-tier deployment without GPU:
--
--   all-MiniLM-L6-v2          →  vector(384)   ← default, ~80MB, no API key
--   gemini-embedding-001      →  vector(3072)  ← free API tier on GEMINI_API_KEY
--                                              (or 1536 / 768 if EMBEDDING_DIM truncates)
--   text-embedding-004        →  vector(768)   ← legacy free Gemini
--
-- If you change EMBEDDING_MODEL, drop and recreate this table with the
-- right dimension OR run an ALTER TABLE migration:
--
--   ALTER TABLE documents ALTER COLUMN embedding TYPE vector(3072);
--
-- (Existing rows must be re-embedded — pgvector won't auto-cast between
-- dimensions.)

create extension if not exists vector;

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  content text not null,
  metadata jsonb default '{}',
  embedding vector(384),
  created_at timestamptz default now()
);

create index if not exists documents_embedding_idx
  on documents using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
