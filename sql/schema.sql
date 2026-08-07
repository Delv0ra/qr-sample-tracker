-- QR Sample Tracker - databasestructuur (v2)
-- Voer dit uit in Supabase: Dashboard -> SQL Editor -> New query -> plak -> Run
--
-- Werkwijze: stalen komen binnen en worden als eerste ingelogd (sample_intakes
-- + samples). Pas later, en niet altijd, wordt daar een werkaanvraag aan
-- gekoppeld (work_requests). Daarom is de koppeling vanaf samples naar
-- work_requests optioneel (nullable), in plaats van verplicht.

-- Opruimen van de oude (MVP-test) tabellen, inclusief de nepdata erin.
drop table if exists samples cascade;
drop table if exists sample_intakes cascade;
drop table if exists work_requests cascade;

-- Tabel 1: work_requests (werkaanvraag - optioneel, komt na de stalen)
-- request_code is het unieke, door de app voorgestelde nummer (bv. "26-S001").
-- custom_fields bevat de waarden van extra, door de admin toegevoegde velden.
create table work_requests (
    id uuid primary key default gen_random_uuid(),
    request_code text not null unique,
    description text not null,
    requester text,
    custom_fields jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

-- Tabel 2: sample_intakes (het moment dat 1 of meerdere stalen binnenkomen
-- en ingelogd worden onder één gezamenlijk batch-nummer, bv. "26-Stijn-001")
-- Categorie heeft geen vaste check-constraint meer: de geldige waarden staan
-- in option_lists (hieronder), beheerbaar door de admin.
create table sample_intakes (
    id uuid primary key default gen_random_uuid(),
    batch_code text not null unique,
    intake_year int not null,
    seq_number int not null,
    logged_by text not null default 'Stijn',
    customer text,
    status text not null default 'ongoing' check (status in ('ongoing', 'complete')),
    category text,
    date_received date not null default current_date,
    date_completed date,
    description text,
    custom_fields jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

-- Tabel: option_lists (door de admin beheerbare keuzelijsten, bv. categorieën)
create table option_lists (
    id uuid primary key default gen_random_uuid(),
    list_key text not null,
    value text not null,
    display_order int not null default 0,
    created_at timestamptz not null default now(),
    unique (list_key, value)
);

insert into option_lists (list_key, value, display_order)
values
    ('category', 'quality control', 1),
    ('category', 'complaint', 2),
    ('category', 'process monitoring', 3);

-- Tabel: field_definitions (door de admin toegevoegde extra velden)
create table field_definitions (
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

-- Tabel 3: samples (elk individueel staal, bv. "26-Stijn-001-01")
create table samples (
    id uuid primary key default gen_random_uuid(),
    intake_id uuid not null references sample_intakes(id) on delete cascade,
    sample_number text not null unique,
    sample_index int not null,
    work_request_id uuid references work_requests(id) on delete set null,
    created_at timestamptz not null default now()
);

-- MVP-fase: geen login nodig voor gewone gebruikers, dus Row Level Security
-- blijft uit (de admin-instellingenpagina heeft een eigen wachtwoordscherm
-- in de app zelf, niet via RLS). Voor een echte klant later: RLS aanzetten
-- + policies toevoegen.
alter table work_requests disable row level security;
alter table sample_intakes disable row level security;
alter table samples disable row level security;
alter table option_lists disable row level security;
alter table field_definitions disable row level security;
