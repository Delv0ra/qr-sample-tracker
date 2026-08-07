import uuid

import streamlit as st

from db import get_client

st.set_page_config(page_title="Bekijk werkaanvraag", page_icon="🔍")
st.title("🔍 Opzoeken")

client = get_client()


def toon_extra_velden(entity: str, custom_fields: dict) -> None:
    velden = (
        client.table("field_definitions")
        .select("*")
        .eq("entity", entity)
        .order("display_order")
        .execute()
        .data
    )
    for veld in velden:
        waarde = (custom_fields or {}).get(veld["field_key"])
        if waarde not in (None, ""):
            st.write(f"**{veld['label']}:** {waarde}")


def toon_intake(intake: dict) -> None:
    st.subheader(intake["batch_code"])
    status_emoji = "✅" if intake["status"] == "complete" else "🔄"
    st.write(f"**Status:** {status_emoji} {intake['status']}")
    st.write(f"**Klant:** {intake['customer'] or '-'}")
    st.write(f"**Categorie:** {intake['category'] or '-'}")
    st.write(f"**Datum binnengekomen:** {intake['date_received']}")
    st.write(f"**Datum voltooid:** {intake['date_completed'] or '-'}")
    st.write(f"**Beschrijving stalen:** {intake['description'] or '-'}")
    toon_extra_velden("sample_intake", intake.get("custom_fields"))

    st.divider()
    st.caption("Stalen in deze batch")
    samples_in_batch = (
        client.table("samples")
        .select("sample_number, work_request_id")
        .eq("intake_id", intake["id"])
        .order("sample_number")
        .execute()
        .data
    )

    wr_ids = {s["work_request_id"] for s in samples_in_batch if s["work_request_id"]}
    wr_lookup = {}
    if wr_ids:
        wr_rows = (
            client.table("work_requests").select("*").in_("id", list(wr_ids)).execute().data
        )
        wr_lookup = {wr["id"]: wr for wr in wr_rows}

    if samples_in_batch:
        for s in samples_in_batch:
            wr = wr_lookup.get(s["work_request_id"])
            koppeling = f" _(werkaanvraag {wr['request_code']})_" if wr else ""
            st.write(f"- {s['sample_number']}{koppeling}")
    else:
        st.info("Geen stalen gevonden in deze batch.")

    if wr_lookup:
        st.divider()
        st.caption("Gekoppelde werkaanvra(a)g(en)")
        for wr in wr_lookup.values():
            st.write(f"**{wr['request_code']}**")
            st.write(f"Beschrijving: {wr['description']}")
            st.write(f"Aanvrager: {wr['requester'] or '-'}")
            st.write(f"Datum aangemaakt: {wr['created_at']}")


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
    toon_extra_velden("sample_intake", intake.get("custom_fields"))

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


query_batch_id = st.query_params.get("batch_id", "")
query_sample_id = st.query_params.get("sample_id", "")
zoekterm = st.text_input(
    "Batch-, staal- of werkaanvraagnummer",
    value=query_batch_id or query_sample_id,
    help=(
        "Wordt automatisch ingevuld als je via een QR-code-link komt. Je kan "
        "hier ook manueel een batchnummer (bv. 26-Stijn-001), staalnummer "
        "(bv. 26-Stijn-001-01), of werkaanvraag-nummer (bv. 26-S001) intypen."
    ),
).strip()

if not zoekterm:
    st.info("Scan een QR-code, of vul hierboven een nummer in.")
    st.stop()

intake = None
sample = None

try:
    uuid.UUID(zoekterm)
    gevonden = client.table("sample_intakes").select("*").eq("id", zoekterm).execute().data
    intake = gevonden[0] if gevonden else None
    if not intake:
        gevonden = client.table("samples").select("*").eq("id", zoekterm).execute().data
        sample = gevonden[0] if gevonden else None
except ValueError:
    pass

if not intake and not sample:
    gevonden = (
        client.table("sample_intakes").select("*").ilike("batch_code", zoekterm).execute().data
    )
    intake = gevonden[0] if gevonden else None

if not intake and not sample:
    gevonden = (
        client.table("samples").select("*").ilike("sample_number", zoekterm).execute().data
    )
    sample = gevonden[0] if gevonden else None

if intake:
    toon_intake(intake)
elif sample:
    toon_staal(sample)
else:
    gevonden_wr = (
        client.table("work_requests").select("*").ilike("request_code", zoekterm).execute().data
    )
    if gevonden_wr:
        toon_werkaanvraag(gevonden_wr[0])
    else:
        st.error(
            "Niets gevonden met dit nummer. Controleer het batch-, staal- of "
            "werkaanvraagnummer."
        )
