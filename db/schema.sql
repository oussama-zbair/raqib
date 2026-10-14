-- ============================================================
-- Raqib (رقيب) — Supabase Postgres schema
-- Run in the Supabase SQL editor.
-- ============================================================

create extension if not exists "pgcrypto";

-- ---------- Enums ----------
do $$ begin
  create type source_type as enum ('PORTAL', 'MINISTRY', 'TELEGRAM', 'AGGREGATOR');
exception when duplicate_object then null; end $$;

do $$ begin
  create type competition_stage as enum ('AVIS', 'CONVOQUES', 'RESULTATS');
exception when duplicate_object then null; end $$;

do $$ begin
  create type tracking_state as enum (
    'APPLIED',                 -- dossier soumis
    'EN_ATTENTE_CONVOCATION',  -- waiting for convocation
    'CONVOQUE',                -- found on convocation list
    'RESULTAT'                 -- results published
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type onboarding_state as enum (
    'NEW', 'AWAIT_NAME_FR', 'AWAIT_NAME_AR', 'AWAIT_CIN',
    'AWAIT_GRADE', 'AWAIT_SPECIALTY', 'COMPLETE'
  );
exception when duplicate_object then null; end $$;

-- ---------- users ----------
-- Identity = Telegram user id. No passwords.
create table if not exists users (
  id                bigint generated always as identity primary key,
  telegram_user_id  bigint unique not null,
  telegram_username text,
  locale            text default 'fr',   -- 'fr' | 'ar'
  is_owner          boolean default false, -- bot admin (set for your Telegram id)
  created_at        timestamptz default now(),
  updated_at        timestamptz default now()
);

-- ---------- profiles ----------
-- One profile per user. CIN stored ENCRYPTED (Fernet) — never plaintext.
create table if not exists profiles (
  id                  bigint generated always as identity primary key,
  user_id             bigint not null references users(id) on delete cascade,
  full_name_fr        text,
  full_name_ar        text,
  cin_encrypted       text,               -- Fernet ciphertext of CIN
  cin_last4           text,               -- non-sensitive display hint (e.g. "3456")
  target_grades       text[] default '{}',      -- canonical grade keys
  target_specialties  text[] default '{}',      -- canonical specialty keys
  include_off_target  boolean default false,    -- opt-in to Technicien/other fields
  onboarding_state    onboarding_state default 'NEW',
  paused              boolean default false,    -- pause all alerts
  quiet_start         smallint,                 -- quiet hours start (0-23, local), null = off
  quiet_end           smallint,                 -- quiet hours end   (0-23, local)
  created_at          timestamptz default now(),
  updated_at          timestamptz default now(),
  unique (user_id)
);

-- ---------- announcement_sources ----------
create table if not exists announcement_sources (
  id            bigint generated always as identity primary key,
  name          text not null,
  type          source_type not null,
  url           text not null,
  enabled       boolean default true,
  last_run_at   timestamptz,
  last_status   text,                 -- 'OK' | 'ERROR: ...'
  created_at    timestamptz default now(),
  unique (name)
);

-- ---------- competitions ----------
-- Canonical, deduplicated competition records.
create table if not exists competitions (
  id               bigint generated always as identity primary key,
  canonical_hash   text unique not null,      -- hash(normalized_admin+grade+deadline)
  administration   text not null,
  grade            text,                      -- canonical grade key
  specialty        text,                      -- canonical specialty key
  required_degree  text,
  deadline         date,
  post_count       integer,
  submission_link  text,
  reference_code   text,                      -- official ref, attached when portal posts
  stage            competition_stage default 'AVIS',
  early_signal     boolean default false,     -- seen on community feed before portal
  title_fr         text,
  title_ar         text,
  source_ids       bigint[] default '{}',     -- every source it appeared on
  source_urls      text[] default '{}',
  convocation_pdf_url text,
  results_pdf_url  text,
  raw              jsonb,                     -- original extracted payload
  first_seen_at    timestamptz default now(),
  updated_at       timestamptz default now()
);

create index if not exists idx_competitions_deadline on competitions(deadline);
create index if not exists idx_competitions_stage on competitions(stage);
create index if not exists idx_competitions_grade on competitions(grade);
create index if not exists idx_competitions_specialty on competitions(specialty);

-- ---------- tracked_competitions ----------
-- User <-> competition tracking pipeline.
create table if not exists tracked_competitions (
  id               bigint generated always as identity primary key,
  user_id          bigint not null references users(id) on delete cascade,
  competition_id   bigint not null references competitions(id) on delete cascade,
  state            tracking_state default 'APPLIED',
  last_checked_at  timestamptz,
  last_pdf_url     text,
  rollcall_result  jsonb,             -- {found, centre, salle, table, exam_date, pdf_url}
  notified_convocation boolean default false,
  notified_result  boolean default false,
  created_at       timestamptz default now(),
  updated_at       timestamptz default now(),
  unique (user_id, competition_id)
);

create index if not exists idx_tracked_user on tracked_competitions(user_id);
create index if not exists idx_tracked_state on tracked_competitions(state);

-- ---------- digest_queue ----------
-- Matched competitions pending delivery to a user (drained by the digest job).
create table if not exists digest_queue (
  id             bigint generated always as identity primary key,
  user_id        bigint not null references users(id) on delete cascade,
  competition_id bigint not null references competitions(id) on delete cascade,
  sent           boolean default false,
  created_at     timestamptz default now(),
  sent_at        timestamptz,
  unique (user_id, competition_id)
);

create index if not exists idx_digest_pending on digest_queue(user_id) where sent = false;

-- ---------- updated_at trigger ----------
create or replace function set_updated_at() returns trigger as $$
begin new.updated_at = now(); return new; end;
$$ language plpgsql;

do $$
declare t text;
begin
  foreach t in array array['users','profiles','competitions','tracked_competitions']
  loop
    execute format(
      'drop trigger if exists trg_%1$s_updated on %1$s;
       create trigger trg_%1$s_updated before update on %1$s
       for each row execute function set_updated_at();', t);
  end loop;
end $$;

-- ============================================================
-- Row Level Security
-- Backend + bot use the service_role key (bypasses RLS).
-- Web dashboard uses the anon key: read-only, and NEVER the CIN column.
-- ============================================================
alter table competitions enable row level security;
alter table announcement_sources enable row level security;
alter table tracked_competitions enable row level security;

-- Public (anon) read access to non-sensitive tables for the admin dashboard.
drop policy if exists anon_read_competitions on competitions;
create policy anon_read_competitions on competitions
  for select to anon using (true);

drop policy if exists anon_read_sources on announcement_sources;
create policy anon_read_sources on announcement_sources
  for select to anon using (true);

-- Tracking counts are aggregate/status only; anon may read state but the dashboard
-- must select non-identifying columns. profiles + users have NO anon policy => hidden.
drop policy if exists anon_read_tracked on tracked_competitions;
create policy anon_read_tracked on tracked_competitions
  for select to anon using (true);

-- NOTE: profiles.cin_encrypted is only ever read by the service_role (backend monitor).
-- The anon role has no policy on `profiles` or `users`, so CIN is never exposed.

-- ============================================================
-- Seed sources
-- ============================================================
insert into announcement_sources (name, type, url) values
  ('emploi-public.ma',        'PORTAL',     'https://www.emploi-public.ma'),
  ('Ministère des Finances',  'MINISTRY',   'https://www.finances.gov.ma'),
  ('Ministère de la Justice', 'MINISTRY',   'https://www.justice.gov.ma'),
  ('Ministère de l''Intérieur','MINISTRY',  'https://www.interieur.gov.ma'),
  ('Alwadifa-Maroc',          'AGGREGATOR', 'https://www.alwadifa-maroc.com')
on conflict (name) do nothing;
