-- =====================================================================
--  BlackMarker.TV live chat — database schema
--  Paste this whole file into the Supabase SQL editor and run it once.
--
--  DESIGN (agreed 2026-08-04, do not re-litigate):
--    * ONE status field drives two surfaces.
--        site chat  -> shows 'live' and 'released'   (NOT release-gated:
--                      a gated site chat feels dead and nobody talks)
--        vMix       -> shows 'released' only
--        'hidden'   -> shows nowhere, on the site or on air
--      One moderator action kills a message in both places. No second
--      system to keep in sync.
--    * Accounts are OPTIONAL via Supabase anonymous sign-in. Every visitor
--      silently gets a real auth identity with no signup form. That is what
--      lets us ban by user_id rather than by IP or a retypeable name, rate
--      limit per person, and let someone upgrade to email/OAuth later while
--      keeping the same id and their history.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. MESSAGES
-- ---------------------------------------------------------------------
create type message_status as enum ('live', 'released', 'hidden');

create table public.messages (
  id           bigint generated always as identity primary key,
  created_at   timestamptz not null default now(),
  user_id      uuid        not null references auth.users(id) on delete cascade,
  display_name text        not null,
  body         text        not null,
  status       message_status not null default 'live',

  -- set when a moderator puts this on air; also the sort key the vMix
  -- feed uses, so re-releasing an older message moves it back to the top
  released_at  timestamptz,
  released_by  uuid references auth.users(id),

  -- true once the visitor signs in with a real identity. The moderator
  -- panel shows a badge for these so they can see who is verified before
  -- putting a name on air — the impersonation mitigation.
  is_verified  boolean not null default false,

  constraint body_not_blank  check (length(btrim(body)) between 1 and 500),
  constraint name_not_blank  check (length(btrim(display_name)) between 1 and 40)
);

-- the site chat reads newest-first over non-hidden rows
create index messages_visible_idx on public.messages (created_at desc)
  where status <> 'hidden';

-- the vMix feed reads the single most recently released message
create index messages_released_idx on public.messages (released_at desc)
  where status = 'released';


-- ---------------------------------------------------------------------
-- 2. BANS  — by user_id, which is the whole point of anonymous auth
-- ---------------------------------------------------------------------
create table public.bans (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  banned_by  uuid references auth.users(id),
  reason     text
);


-- ---------------------------------------------------------------------
-- 3. MODERATORS  — explicit allow-list. Nobody is a moderator by default,
--    including you: add your own user_id after your first sign-in.
-- ---------------------------------------------------------------------
create table public.moderators (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  note       text
);

create or replace function public.is_moderator()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (select 1 from public.moderators where user_id = auth.uid());
$$;


-- ---------------------------------------------------------------------
-- 4. POSTING RULES — enforced in the database, not the browser.
--    Anything enforced only in JavaScript is a suggestion.
-- ---------------------------------------------------------------------
create or replace function public.check_message_allowed()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  recent_count int;
begin
  -- banned users cannot post
  if exists (select 1 from public.bans where user_id = auth.uid()) then
    raise exception 'banned';
  end if;

  -- rate limit: 5 messages per 15 seconds per person
  select count(*) into recent_count
  from public.messages
  where user_id = auth.uid()
    and created_at > now() - interval '15 seconds';

  if recent_count >= 5 then
    raise exception 'rate_limited';
  end if;

  -- a poster never chooses their own status or release state
  new.status      := 'live';
  new.released_at := null;
  new.released_by := null;
  new.user_id     := auth.uid();
  return new;
end;
$$;

create trigger messages_before_insert
  before insert on public.messages
  for each row execute function public.check_message_allowed();


-- keep released_at honest no matter who writes the row
create or replace function public.stamp_release()
returns trigger
language plpgsql
as $$
begin
  if new.status = 'released' and (old.status is distinct from 'released') then
    new.released_at := now();
    new.released_by := auth.uid();
  end if;
  return new;
end;
$$;

create trigger messages_before_update
  before update on public.messages
  for each row execute function public.stamp_release();


-- ---------------------------------------------------------------------
-- 5. ROW LEVEL SECURITY
-- ---------------------------------------------------------------------
alter table public.messages   enable row level security;
alter table public.bans       enable row level security;
alter table public.moderators enable row level security;

-- anyone, signed in or anonymous, can read everything that is not hidden
create policy messages_read_visible
  on public.messages for select
  using (status <> 'hidden');

-- moderators can read everything, including hidden, so they can review
create policy messages_read_all_mods
  on public.messages for select
  using (public.is_moderator());

-- any authenticated identity may post as itself; the trigger does the rest
create policy messages_insert_own
  on public.messages for insert
  with check (auth.uid() = user_id);

-- ONLY moderators can change a message's status
create policy messages_update_mods
  on public.messages for update
  using (public.is_moderator())
  with check (public.is_moderator());

create policy messages_delete_mods
  on public.messages for delete
  using (public.is_moderator());

-- bans and the moderator list are moderator-only in both directions
create policy bans_all_mods
  on public.bans for all
  using (public.is_moderator())
  with check (public.is_moderator());

create policy mods_read_self
  on public.moderators for select
  using (user_id = auth.uid() or public.is_moderator());


-- ---------------------------------------------------------------------
-- 6. REALTIME — the site chat and the overlay both subscribe to this
-- ---------------------------------------------------------------------
alter publication supabase_realtime add table public.messages;


-- ---------------------------------------------------------------------
-- 7. AFTER RUNNING THIS
--
--   a) Authentication -> Providers -> enable "Anonymous sign-ins".
--   b) Load the site once so you get an anonymous identity, then find your
--      id under Authentication -> Users and make yourself a moderator:
--
--        insert into public.moderators (user_id, note)
--        values ('PASTE-YOUR-UUID-HERE', 'Eric');
--
--   c) Nothing else is a moderator until you add it. The panel is useless
--      to anyone who is not on that list, even if they find the URL.
-- ---------------------------------------------------------------------
