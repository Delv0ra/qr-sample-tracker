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
create table work_requests (
    id uuid primary key default gen_random_uuid(),
    request_code text not null unique,
    description text not null,
    requester text,
    created_at timestamptz not null default now()
);

-- Tabel 2: sample_intakes (het moment dat 1 of meerdere stalen binnenkomen
-- en ingelogd worden onder één gezamenlijk batch-nummer, bv. "26-Stijn-001")
create table sample_intakes (
    id uuid primary key default gen_random_uuid(),
    batch_code text not null unique,
    intake_year int not null,
    seq_number int not null,
    logged_by text not null default 'Stijn',
    customer text,
    status text not null default 'ongoing' check (status in ('ongoing', 'complete')),
    category text check (category in ('quality control', 'complaint', 'process monitoring')),
    date_received date not null default current_date,
    date_completed date,
    description text,
    created_at timestamptz not null default now()
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

-- MVP-fase: geen login nodig, dus Row Level Security blijft uit.
-- Voor een echte klant later: RLS aanzetten + policies toevoegen.
alter table work_requests disable row level security;
alter table sample_intakes disable row level security;
alter table samples disable row level security;
