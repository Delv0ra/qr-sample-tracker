import datetime

import streamlit as st

from db import get_client

st.set_page_config(page_title="Werkaanvraag aanmaken", page_icon="📝")
st.title("📝 Werkaanvraag aanmaken")

client = get_client()


def volgende_werkaanvraag_code(year: int) -> str:
    """Geeft het volgende voorstelnummer (bv. '26-S003') voor het opgegeven jaar."""
    yy = str(year)[-2:]
    prefix = f"{yy}-S"
    bestaande = (
        client.table("work_requests")
        .select("request_code")
        .like("request_code", f"{prefix}%")
        .execute()
        .data
    )
    nummers = [
        int(row["request_code"][len(prefix):])
        for row in bestaande
        if row["request_code"][len(prefix):].isdigit()
    ]
    volgnummer = max(nummers, default=0) + 1
    return f"{prefix}{volgnummer:03d}"


if "wr_form_lichting" not in st.session_state:
    st.session_state.wr_form_lichting = 0

if "wr_laatste_melding" in st.session_state:
    st.success(st.session_state.pop("wr_laatste_melding"))

voorstel_code = volgende_werkaanvraag_code(datetime.date.today().year)

request_code = st.text_input(
    "Werkaanvraag-nummer",
    value=voorstel_code,
    key=f"request_code_input_{st.session_state.wr_form_lichting}",
    help=(
        "Wordt automatisch voorgesteld. Pas dit aan naar een bestaand nummer "
        "om stalen toe te voegen aan een werkaanvraag die al bestaat (bv. "
        "stalen die op een later moment zijn binnengekomen)."
    ),
).strip()

bestaande_wr = None
if request_code:
    gevonden = (
        client.table("work_requests")
        .select("*")
        .eq("request_code", request_code)
        .execute()
        .data
    )
    bestaande_wr = gevonden[0] if gevonden else None

if bestaande_wr:
    st.info(
        f"Bestaande werkaanvraag **{request_code}**: \"{bestaande_wr['description']}\" "
        f"(aanvrager: {bestaande_wr['requester'] or '-'}). De gekozen stalen worden "
        "hieraan toegevoegd."
    )
else:
    st.caption("Nieuw nummer — vul hieronder de gegevens voor de nieuwe werkaanvraag in.")
    description = st.text_area("Beschrijving van de werkaanvraag *")
    requester = st.text_input("Aanvrager")

st.divider()

intakes = (
    client.table("sample_intakes")
    .select("id, batch_code, customer")
    .order("created_at", desc=True)
    .execute()
    .data
)

if not intakes:
    st.warning(
        "Er zijn nog geen stalen ingelogd. Log eerst stalen in op de pagina "
        "'Stalen Inloggen'."
    )
    st.stop()

intake_opties = {f"{i['batch_code']} - {i['customer'] or 'onbekende klant'}": i["id"] for i in intakes}
gekozen_label = st.selectbox("Staal-nummer (batch) *", options=list(intake_opties.keys()))
intake_id = intake_opties[gekozen_label]

samples = (
    client.table("samples")
    .select("id, sample_number")
    .eq("intake_id", intake_id)
    .order("sample_index")
    .execute()
    .data
)

alle_toevoegen = st.checkbox(
    f"Alle {len(samples)} stalen van dit nummer toevoegen", value=True
)

if alle_toevoegen:
    geselecteerde_ids = [s["id"] for s in samples]
    st.write(", ".join(s["sample_number"] for s in samples))
else:
    sample_opties = {s["sample_number"]: s["id"] for s in samples}
    gekozen_samples = st.multiselect("Kies specifieke stalen", options=list(sample_opties.keys()))
    geselecteerde_ids = [sample_opties[s] for s in gekozen_samples]

knop_tekst = "Stalen toevoegen aan werkaanvraag" if bestaande_wr else "Werkaanvraag aanmaken"

if st.button(knop_tekst):
    if not request_code:
        st.error("Werkaanvraag-nummer is verplicht.")
    elif not bestaande_wr and not description.strip():
        st.error("Beschrijving is verplicht.")
    elif not geselecteerde_ids:
        st.error("Kies minstens één staal om aan de werkaanvraag te koppelen.")
    else:
        if bestaande_wr:
            wr_id = bestaande_wr["id"]
        else:
            wr = (
                client.table("work_requests")
                .insert(
                    {
                        "request_code": request_code,
                        "description": description.strip(),
                        "requester": requester.strip(),
                    }
                )
                .execute()
                .data[0]
            )
            wr_id = wr["id"]

        client.table("samples").update({"work_request_id": wr_id}).in_(
            "id", geselecteerde_ids
        ).execute()

        st.session_state.wr_laatste_melding = (
            f"{len(geselecteerde_ids)} staal/stalen gekoppeld aan werkaanvraag {request_code}."
        )
        st.session_state.wr_form_lichting += 1
        st.rerun()
