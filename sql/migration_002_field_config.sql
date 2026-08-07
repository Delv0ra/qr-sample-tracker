-- Migratie 002: instelbare velden voor de admin
-- Voer dit uit in Supabase: Dashboard -> SQL Editor -> New query -> plak -> Run
--
-- Dit is een TOEVOEGENDE migratie (geen drop table): bestaande data blijft
-- gewoon staan.

-- Categorie kreeg tot nu toe een vaste lijst via een check-constraint op
-- databaseniveau. Die lijst wordt voortaan beheerd via option_lists
-- (hieronder), dus de oude constraint laten we los.
alter table sample_intakes drop constraint if exists sample_intakes_category_check;

-- Plek om door de admin beheerbare keuzelijsten op te slaan (bv. categorieën).
create table if not exists option_lists (
    id uuid primary key default gen_random_uuid(),
    list_key text not null,
    value text not null,
    display_order int not null default 0,
    created_at timestamptz not null default now(),
    unique (list_key, value)
);
alter table option_lists disable row level security;

-- De 3 bestaande categorieën overzetten naar de nieuwe, beheerbare lijst.
insert into option_lists (list_key, value, display_order)
values
    ('category', 'quality control', 1),
    ('category', 'complaint', 2),
    ('category', 'process monitoring', 3)
on conflict (list_key, value) do nothing;

-- Definities van extra, door de admin toegevoegde velden (per entiteit).
create table if not exists field_definitions (
    id uuid primary key default gen_random_uuid(),
    entity text not null check (entity in ('sample_intake', 'work_request')),
    field_key text not null,
    label text not null,
    field_type text not null check (field_type in ('text', 'number', 'date', 'boolean', 'select')),
    options jsonb,
    required boolean not null default false,
    display_order int not null default 0,
    created_at timestamptz not null default now(),
    unique (entity, field_key)
);
alter table field_definitions disable row level security;

-- Opslagplaats voor de ingevulde waarden van die extra velden.
alter table sample_intakes add column if not exists custom_fields jsonb not null default '{}'::jsonb;
alter table work_requests add column if not exists custom_fields jsonb not null default '{}'::jsonb;
