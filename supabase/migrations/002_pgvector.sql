create extension if not exists vector;

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  content text not null,
  metadata jsonb default '{}',
  embedding vector(384),
  created_at timestamptz default now()
);

create index on documents using ivfflat (embedding vector_cosine_ops) with (lists = 100);
