import uuid

import streamlit as st

from db import get_client

st.set_page_config(page_title="Bekijk werkaanvraag", page_icon="🔍")
st.title("🔍 Opzoeken")

client = get_client()


def toon_staal(sample: dict) -> None:
    intake_result = (
        client.table("sample_intakes").select("*").eq("id", sample["intake_id"]).execute()
    )
    if not intake_result.data:
        st.error("Gekoppelde staal-intake niet gevonden.")
        return
    intake = intake_result.data[0]

    st.subheader(sample["sample_number"])
    status_emoji = "✅" if intake["status"] == "complete" else "🔄"
    st.write(f"**Status:** {status_emoji} {intake['status']}")
    st.write(f"**Klant:** {intake['customer'] or '-'}")
    st.write(f"**Categorie:** {intake['category'] or '-'}")
    st.write(f"**Datum binnengekomen:** {intake['date_received']}")
    st.write(f"**Datum voltooid:** {intake['date_completed'] or '-'}")
    st.write(f"**Beschrijving stalen:** {intake['description'] or '-'}")

    st.divider()
    st.caption("Gekoppelde werkaanvraag")

    if sample["work_request_id"]:
        wr_result = (
            client.table("work_requests")
            .select("*")
            .eq("id", sample["work_request_id"])
            .execute()
        )
        if wr_result.data:
            wr = wr_result.data[0]
            st.write(f"**Nummer:** {wr['request_code']}")
            st.write(f"**Beschrijving:** {wr['description']}")
            st.write(f"**Aanvrager:** {wr['requester'] or '-'}")
            st.write(f"**Datum aangemaakt:** {wr['created_at']}")
        else:
            st.warning("Gekoppelde werkaanvraag niet gevonden.")
    else:
        st.info("Nog geen werkaanvraag gekoppeld aan dit staal.")


def toon_werkaanvraag(wr: dict) -> None:
    st.subheader(wr["request_code"])
    st.write(f"**Beschrijving:** {wr['description']}")
    st.write(f"**Aanvrager:** {wr['requester'] or '-'}")
    st.write(f"**Datum aangemaakt:** {wr['created_at']}")

    st.divider()
    st.caption("Gekoppelde stalen")
    gekoppelde_samples = (
        client.table("samples")
        .select("sample_number")
        .eq("work_request_id", wr["id"])
        .order("sample_number")
        .execute()
        .data
    )
    if gekoppelde_samples:
        for s in gekoppelde_samples:
            st.write(f"- {s['sample_number']}")
    else:
        st.info("Nog geen stalen gekoppeld aan deze werkaanvraag.")


query_sample_id = st.query_params.get("sample_id", "")
zoekterm = st.text_input(
    "Sample-nummer of werkaanvraag-nummer",
    value=query_sample_id,
    help=(
        "Wordt automatisch ingevuld als je via een QR-code-link komt. Je kan "
        "hier ook manueel een staalnummer (bv. 26-Stijn-001-01) of een "
        "werkaanvraag-nummer (bv. 26-S001) intypen."
    ),
).strip()

if not zoekterm:
    st.info("Scan een QR-code, of vul hierboven een nummer in.")
    st.stop()

sample = None

try:
    uuid.UUID(zoekterm)
    gevonden = client.table("samples").select("*").eq("id", zoekterm).execute().data
    sample = gevonden[0] if gevonden else None
except ValueError:
    pass

if not sample:
    gevonden = (
        client.table("samples").select("*").ilike("sample_number", zoekterm).execute().data
    )
    sample = gevonden[0] if gevonden else None

if sample:
    toon_staal(sample)
else:
    gevonden_wr = (
        client.table("work_requests").select("*").ilike("request_code", zoekterm).execute().data
    )
    if gevonden_wr:
        toon_werkaanvraag(gevonden_wr[0])
    else:
        st.error("Niets gevonden met dit nummer. Controleer het staalnummer of werkaanvraag-nummer.")
