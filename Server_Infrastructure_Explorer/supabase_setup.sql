-- Run once in your Supabase project's SQL editor. No credentials belong here.
create table if not exists public.server_tutor_learners (
  id text primary key check (id ~ '^[0-9a-f]{64}$'),
  payload jsonb not null check (jsonb_typeof(payload) = 'object'),
  updated_at timestamptz not null default now()
);
alter table public.server_tutor_learners enable row level security;
revoke all on public.server_tutor_learners from anon, authenticated;
grant select, insert, update on public.server_tutor_learners to service_role;
-- No public RLS policies. Only the Python server holds the secret key.
-- Each request is scoped by a SHA-256 hash of the private recovery code.
