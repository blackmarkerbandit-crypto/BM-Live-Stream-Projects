-- =====================================================================
--  BlackMarker.TV chat — MIGRATION v2: rooms, per-room moderators, admin
--
--  Run ONCE in the Supabase SQL editor, after schema.sql.
--  Safe to run against the live table: existing messages are preserved and
--  land in the 'main' room. Existing global moderators stay global and are
--  promoted to admins so you cannot lock yourself out.
--
--  WHAT THIS BUYS YOU
--    * Many chats on one stack. A PPV event gets its own room; nothing
--      crosses between rooms in any UI or on air.
--    * Moderators scoped per room. A PPV moderator cannot touch the main
--      channel, and vice versa. Room '*' means every room.
--    * An admin tier that can create rooms and appoint moderators.
--    * A profiles table so the admin page can list actual chatters without
--      ever needing the service_role key in a browser.
--
--  WHAT IT DOES NOT BUY YOU  -- read this before selling a PPV ticket
--    The anon key is public by design. A room's isolation is only as strong
--    as its visibility setting:
--      'public'     listed, anyone reads and posts
--      'unlisted'   not listed anywhere, but anyone who learns the slug can
--                   read and post. Good enough when the CMS gates the page
--                   and the slug is not guessable. NOT a cryptographic wall.
--      'restricted' only rows in room_members may read or post. This is the
--                   real gate, and it needs something server-side (a CMS
--                   webhook using the service_role key) to add members.
--    Pick 'unlisted' for a PPV room today; move to 'restricted' the day the
--    CMS can tell Supabase who paid. Nothing else has to change.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. ROOMS
-- ---------------------------------------------------------------------
create table if not exists public.rooms (
  slug        text primary key
              check (slug ~ '^[a-z0-9][a-z0-9_-]{1,60}$'),
  name        text not null,
  visibility  text not null default 'public'
              check (visibility in ('public', 'unlisted', 'restricted')),
  archived    boolean not null default false,   -- read-only, still readable
  created_at  timestamptz not null default now(),
  note        text
);

-- the room every existing message belongs to
insert into public.rooms (slug, name, visibility, note)
values ('main', 'BlackMarker.TV', 'public', 'The 24/7 channel. Created by the v2 migration.')
on conflict (slug) do nothing;


-- ---------------------------------------------------------------------
-- 2. MESSAGES GET A ROOM
--    Default 'main' means every existing row, and any client not yet
--    updated, keeps working exactly as before.
-- ---------------------------------------------------------------------
alter table public.messages
  add column if not exists room text not null default 'main';

do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'messages_room_fk'
  ) then
    alter table public.messages
      add constraint messages_room_fk foreign key (room)
      references public.rooms(slug) on update cascade;
  end if;
end $$;

-- old indexes did not know about rooms; every read is now room-scoped
drop index if exists messages_visible_idx;
drop index if exists messages_released_idx;

create index if not exists messages_room_visible_idx
  on public.messages (room, created_at desc) where status <> 'hidden';

create index if not exists messages_room_released_idx
  on public.messages (room, released_at desc) where status = 'released';


-- ---------------------------------------------------------------------
-- 3. PER-ROOM MODERATORS AND BANS
--    room = '*' means all rooms. A sentinel rather than NULL, because
--    NULL never equals NULL and would break the primary key.
-- ---------------------------------------------------------------------
alter table public.moderators add column if not exists room text not null default '*';
alter table public.moderators drop constraint if exists moderators_pkey;
do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'moderators_pkey') then
    alter table public.moderators add primary key (user_id, room);
  end if;
end $$;

alter table public.bans add column if not exists room text not null default '*';
alter table public.bans drop constraint if exists bans_pkey;
do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'bans_pkey') then
    alter table public.bans add primary key (user_id, room);
  end if;
end $$;


-- ---------------------------------------------------------------------
-- 4. ADMINS — can create rooms and appoint moderators. Moderating is not
--    the same power as deciding who moderates, so it is its own table.
-- ---------------------------------------------------------------------
create table if not exists public.admins (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  note       text
);

-- Anyone who was a global moderator before this migration becomes an admin.
-- Without this you would have no admin at all and no way to appoint one
-- except by hand in SQL.
insert into public.admins (user_id, note)
select user_id, 'promoted by v2 migration (was a global moderator)'
from public.moderators
where room = '*'
on conflict (user_id) do nothing;


-- ---------------------------------------------------------------------
-- 5. ROOM MEMBERS — only consulted for 'restricted' rooms.
--    Empty today. When the CMS can confirm a purchase, it inserts a row
--    here with the service_role key and the room becomes genuinely gated.
-- ---------------------------------------------------------------------
create table if not exists public.room_members (
  room       text not null references public.rooms(slug) on delete cascade,
  user_id    uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  note       text,
  primary key (room, user_id)
);


-- ---------------------------------------------------------------------
-- 6. PROFILES — one row per chatter, maintained by the insert trigger.
--    Lets the admin page list real people to ban or promote without ever
--    putting the service_role key in a browser page.
-- ---------------------------------------------------------------------
create table if not exists public.profiles (
  user_id      uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  first_seen   timestamptz not null default now(),
  last_seen    timestamptz not null default now(),
  message_count integer not null default 0
);


-- ---------------------------------------------------------------------
-- 7. FUNCTIONS
--    The old zero-argument is_moderator() has to go before the new
--    one-argument version exists, or a bare is_moderator() call becomes
--    ambiguous between the two. Policies that depend on it are dropped
--    first, and rebuilt in section 8.
-- ---------------------------------------------------------------------
drop policy if exists messages_read_visible  on public.messages;
drop policy if exists messages_read_all_mods on public.messages;
drop policy if exists messages_insert_own    on public.messages;
drop policy if exists messages_update_mods   on public.messages;
drop policy if exists messages_delete_mods   on public.messages;
drop policy if exists bans_all_mods          on public.bans;
drop policy if exists mods_read_self         on public.moderators;

drop function if exists public.is_moderator();

create or replace function public.is_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.admins where user_id = auth.uid());
$$;

-- true if the caller moderates this specific room (or every room, or is an admin)
create or replace function public.is_moderator(p_room text)
returns boolean language sql stable security definer set search_path = public as $$
  select public.is_admin() or exists (
    select 1 from public.moderators m
    where m.user_id = auth.uid()
      and (m.room = '*' or m.room = p_room)
  );
$$;

-- true if the caller is allowed to see this room at all
create or replace function public.can_read_room(p_room text)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.rooms r
    where r.slug = p_room
      and (
        r.visibility in ('public', 'unlisted')
        or exists (
          select 1 from public.room_members rm
          where rm.room = r.slug and rm.user_id = auth.uid()
        )
      )
  ) or public.is_moderator(p_room);
$$;


-- posting rules, now room-aware
create or replace function public.check_message_allowed()
returns trigger language plpgsql security definer set search_path = public as $$
declare
  recent_count int;
begin
  -- banned from this room, or banned everywhere
  if exists (
    select 1 from public.bans
    where user_id = auth.uid() and (room = '*' or room = new.room)
  ) then
    raise exception 'banned';
  end if;

  -- an archived room is read-only
  if exists (select 1 from public.rooms where slug = new.room and archived) then
    raise exception 'room_archived';
  end if;

  -- rate limit: 5 messages per 15 seconds per person, across all rooms
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

  -- keep a profile row current so the admin page has someone to act on
  insert into public.profiles (user_id, display_name, message_count)
  values (auth.uid(), new.display_name, 1)
  on conflict (user_id) do update
    set display_name  = excluded.display_name,
        last_seen     = now(),
        message_count = public.profiles.message_count + 1;

  return new;
end;
$$;


-- ---------------------------------------------------------------------
-- 8. ROW LEVEL SECURITY
-- ---------------------------------------------------------------------
alter table public.rooms        enable row level security;
alter table public.admins       enable row level security;
alter table public.room_members enable row level security;
alter table public.profiles     enable row level security;

-- MESSAGES ---------------------------------------------------------
-- read: not hidden, and only in a room you are allowed to see
create policy messages_read_visible on public.messages for select
  using (status <> 'hidden' and public.can_read_room(room));

-- moderators of a room see everything in it, hidden included
create policy messages_read_all_mods on public.messages for select
  using (public.is_moderator(room));

-- post as yourself, only into a room you can see
create policy messages_insert_own on public.messages for insert
  with check (auth.uid() = user_id and public.can_read_room(room));

-- only that room's moderators can change or remove its messages
create policy messages_update_mods on public.messages for update
  using (public.is_moderator(room)) with check (public.is_moderator(room));

create policy messages_delete_mods on public.messages for delete
  using (public.is_moderator(room));

-- ROOMS ------------------------------------------------------------
-- 'unlisted' lives up to its name: it is readable but never listed
create policy rooms_read_public on public.rooms for select
  using (visibility = 'public' or public.is_moderator(slug));

create policy rooms_write_admin on public.rooms for all
  using (public.is_admin()) with check (public.is_admin());

-- MODERATORS -------------------------------------------------------
create policy mods_read_self on public.moderators for select
  using (user_id = auth.uid() or public.is_moderator(room));

create policy mods_write_admin on public.moderators for all
  using (public.is_admin()) with check (public.is_admin());

-- ADMINS -----------------------------------------------------------
create policy admins_read on public.admins for select
  using (user_id = auth.uid() or public.is_admin());

create policy admins_write on public.admins for all
  using (public.is_admin()) with check (public.is_admin());

-- BANS -------------------------------------------------------------
create policy bans_all_mods on public.bans for all
  using (public.is_moderator(room)) with check (public.is_moderator(room));

-- ROOM MEMBERS -----------------------------------------------------
create policy room_members_read on public.room_members for select
  using (user_id = auth.uid() or public.is_moderator(room));

create policy room_members_write_admin on public.room_members for all
  using (public.is_admin()) with check (public.is_admin());

-- PROFILES ---------------------------------------------------------
-- moderators need to see who they are moderating; nobody else needs the list
create policy profiles_read_mods on public.profiles for select
  using (user_id = auth.uid() or public.is_admin()
         or exists (select 1 from public.moderators where user_id = auth.uid()));

create policy profiles_write_admin on public.profiles for all
  using (public.is_admin()) with check (public.is_admin());


-- ---------------------------------------------------------------------
-- 9. BACKFILL profiles from the messages already in the table, so the
--    admin page is not empty on day one.
-- ---------------------------------------------------------------------
insert into public.profiles (user_id, display_name, first_seen, last_seen, message_count)
select user_id,
       (array_agg(display_name order by created_at desc))[1],
       min(created_at), max(created_at), count(*)
from public.messages
group by user_id
on conflict (user_id) do nothing;


-- ---------------------------------------------------------------------
-- 10. AFTER RUNNING THIS
--
--   a) Confirm you are an admin (should return true while signed in as
--      blackmarkertv@gmail.com):
--        select public.is_admin();
--
--   b) Everything else is done from admin.html — create rooms, appoint
--      per-room moderators, ban people. No more hand-written SQL.
--
--   c) To create a PPV room by hand instead:
--        insert into public.rooms (slug, name, visibility, note)
--        values ('ppv-2026-11-14', 'November PPV', 'unlisted', 'gated by the CMS page');
--      then embed the chat with ?room=ppv-2026-11-14
-- ---------------------------------------------------------------------
