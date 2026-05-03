-- pgvector schema for the RAG documents table.
--
-- The vector dimension MUST match the embedding model in
-- packages/rag/agentos_rag/embeddings.py. Defaults:
--
--   all-MiniLM-L6-v2     →  vector(384)   ← default, ships in the boilerplate
--   BAAI/bge-m3          →  vector(1024)  ← recommended free upgrade (multilingual, MIT)
--   intfloat/e5-large    →  vector(1024)
--   Qwen/Qwen3-Embedding-8B → vector(7168)
--   nvidia/NV-Embed-v2   →  vector(4096)
--
-- If you change EMBEDDING_MODEL, drop and recreate this table with the
-- right dimension OR run an ALTER TABLE migration:
--
--   ALTER TABLE documents ALTER COLUMN embedding TYPE vector(1024);
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
