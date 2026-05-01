create table if not exists chat_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id),
  title text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists chat_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references chat_sessions(id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'system')),
  content text not null,
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

create index on chat_messages(session_id, created_at);

create table if not exists agent_runs (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references chat_sessions(id),
  status text not null default 'pending',
  task text not null,
  result jsonb,
  provider text,
  latency_ms float,
  created_at timestamptz default now(),
  completed_at timestamptz
);
