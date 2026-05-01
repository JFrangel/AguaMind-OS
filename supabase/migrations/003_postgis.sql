create extension if not exists postgis;

create table if not exists locations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  address text,
  geom geometry(Point, 4326),
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

create index on locations using gist (geom);
