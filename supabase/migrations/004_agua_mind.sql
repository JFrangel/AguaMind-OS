-- AguaMind OS — Water management schema
-- UNIAJC Sede Sur · Hackathon 2026

-- ── Sensor readings (time-series) ─────────────────────────────────────────
create table if not exists water_readings (
  id            bigserial primary key,
  recorded_at   timestamptz not null default now(),
  inflow_l_min  numeric(10,3) not null,
  demand_l_min  numeric(10,3) not null,
  losses_l_min  numeric(10,3) not null,
  tank_a_pct    numeric(5,1) not null,
  tank_b_pct    numeric(5,1) not null,
  scenario      text not null default 'normal'
                check (scenario in ('normal', 'leak', 'peak_irrigation')),
  raw_zones     jsonb not null default '{}'
);

create index on water_readings(recorded_at desc);

-- ── Zone consumption snapshots ─────────────────────────────────────────────
create table if not exists water_zone_readings (
  id          bigserial primary key,
  reading_id  bigint references water_readings(id) on delete cascade,
  zone_name   text not null,
  flow_l_min  numeric(10,3) not null
);

create index on water_zone_readings(reading_id);

-- ── KPI snapshots ──────────────────────────────────────────────────────────
create table if not exists water_kpi_snapshots (
  id          bigserial primary key,
  reading_id  bigint references water_readings(id) on delete cascade,
  kpi_name    text not null check (kpi_name in ('IEH', 'TPP', 'CPE')),
  value       numeric(10,4) not null,
  status      text not null check (status in ('ok', 'warning', 'critical')),
  recorded_at timestamptz not null default now()
);

create index on water_kpi_snapshots(recorded_at desc, kpi_name);

-- ── Alerts log ─────────────────────────────────────────────────────────────
create table if not exists water_alerts (
  id           bigserial primary key,
  reading_id   bigint references water_readings(id) on delete cascade,
  level        text not null check (level in ('critical', 'warning', 'info')),
  zone         text not null,
  message      text not null,
  action       text not null,
  resolved     boolean not null default false,
  resolved_at  timestamptz,
  created_at   timestamptz not null default now()
);

create index on water_alerts(created_at desc);
create index on water_alerts(resolved, level);

-- ── Useful views ───────────────────────────────────────────────────────────

-- Last 24h hourly aggregation for charts
create or replace view water_hourly_summary as
select
  date_trunc('hour', recorded_at)       as hour,
  avg(inflow_l_min)                     as avg_inflow,
  avg(demand_l_min)                     as avg_demand,
  avg(losses_l_min)                     as avg_losses,
  avg(tank_a_pct)                       as avg_tank_a,
  avg(tank_b_pct)                       as avg_tank_b,
  count(*)                              as sample_count
from water_readings
where recorded_at > now() - interval '24 hours'
group by 1
order by 1 desc;

-- Today's KPI summary
create or replace view water_kpi_today as
select
  kpi_name,
  avg(value)      as avg_value,
  min(value)      as min_value,
  max(value)      as max_value,
  mode() within group (order by status) as dominant_status,
  count(*)        as readings
from water_kpi_snapshots
where recorded_at > current_date
group by kpi_name;
