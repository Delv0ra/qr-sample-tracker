import datetime
import io

import qrcode
import streamlit as st

from db import APP_BASE_URL, get_client

st.set_page_config(page_title="Stalen inloggen", page_icon="📦")
st.title("📦 Stalen inloggen")

LOGGED_BY = "Stijn"  # Voorlopig vast; later evt. per gebruiker instelbaar.

client = get_client()


def haal_categorieen() -> list[str]:
    """Categorieën zijn admin-beheerbaar via de Instellingen-pagina i.p.v.
    hardcoded in de code."""
    rows = (
        client.table("option_lists")
        .select("value")
        .eq("list_key", "category")
        .order("display_order")
        .execute()
        .data
    )
    return [r["value"] for r in rows]


categorieen = haal_categorieen()
if not categorieen:
    st.error(
        "Er zijn nog geen categorieën ingesteld. Vraag de beheerder om er "
        "minstens één toe te voegen via de pagina 'Instellingen'."
    )
    st.stop()


def haal_extra_velden() -> list[dict]:
    """Door de admin toegevoegde extra velden (Instellingen-pagina)."""
    return (
        client.table("field_definitions")
        .select("*")
        .eq("entity", "sample_intake")
        .order("display_order")
        .execute()
        .data
    )


extra_velden = haal_extra_velden()


def volgend_batchnummer(year: int) -> tuple[int, str]:
    """Geeft het volgende volgnummer (bv. 3) en de bijhorende batch-code
    (bv. '26-Stijn-003') voor het opgegeven jaar en LOGGED_BY."""
    bestaande = (
        client.table("sample_intakes")
        .select("seq_number")
        .eq("intake_year", year)
        .eq("logged_by", LOGGED_BY)
        .order("seq_number", desc=True)
        .limit(1)
        .execute()
        .data
    )
    volgnummer = (bestaande[0]["seq_number"] + 1) if bestaande else 1
    yy = str(year)[-2:]
    batch_code = f"{yy}-{LOGGED_BY}-{volgnummer:03d}"
    return volgnummer, batch_code


voorstel_placeholder = st.empty()


def toon_voorstel() -> None:
    _, code = volgend_batchnummer(datetime.date.today().year)
    voorstel_placeholder.info(f"Volgend nummer: **{code}**")


toon_voorstel()
st.caption(
    "Dit nummer wordt pas definitief bevestigd op het moment dat je opslaat "
    "(voor het geval er ondertussen iemand anders inlogt)."
)

with st.form("stalen_inloggen", clear_on_submit=True):
    customer = st.text_input("Klant *")
    aantal = st.number_input("Aantal stalen *", min_value=1, value=1, step=1)
    date_received = st.date_input("Datum binnengekomen", value=datetime.date.today())
    category = st.selectbox("Categorie", options=categorieen)
    description = st.text_area("Korte beschrijving van de stalen")

    extra_waarden = {}
    if extra_velden:
        st.divider()
        st.caption("Extra velden")
        for veld in extra_velden:
            label = veld["label"] + (" *" if veld["required"] else "")
            key = f"extra_{veld['field_key']}"
            if veld["field_type"] == "text":
                extra_waarden[veld["field_key"]] = st.text_input(label, key=key)
            elif veld["field_type"] == "number":
                extra_waarden[veld["field_key"]] = st.number_input(label, value=0, key=key)
            elif veld["field_type"] == "date":
                extra_waarden[veld["field_key"]] = st.date_input(label, key=key)
            elif veld["field_type"] == "boolean":
                extra_waarden[veld["field_key"]] = st.checkbox(label, key=key)
            elif veld["field_type"] == "select":
                extra_waarden[veld["field_key"]] = st.selectbox(
                    label, options=veld["options"] or [], key=key
                )

    submitted = st.form_submit_button("Stalen inloggen + QR's genereren")

if submitted:
    if not customer.strip():
        st.error("Klant is verplicht.")
        st.stop()

    for veld in extra_velden:
        if veld["required"] and veld["field_type"] in ("text", "select"):
            if not extra_waarden.get(veld["field_key"]):
                st.error(f"'{veld['label']}' is verplicht.")
                st.stop()

    custom_field_values = {}
    for veld in extra_velden:
        waarde = extra_waarden[veld["field_key"]]
        if veld["field_type"] == "date" and waarde:
            waarde = waarde.isoformat()
        custom_field_values[veld["field_key"]] = waarde

    year = date_received.year
    volgnummer, batch_code = volgend_batchnummer(year)

    intake = (
        client.table("sample_intakes")
        .insert(
            {
                "batch_code": batch_code,
                "intake_year": year,
                "seq_number": volgnummer,
                "logged_by": LOGGED_BY,
                "customer": customer.strip(),
                "category": category,
                "date_received": date_received.isoformat(),
                "description": description.strip(),
                "custom_fields": custom_field_values,
            }
        )
        .execute()
        .data[0]
    )

    nieuwe_samples = []
    for i in range(1, int(aantal) + 1):
        sample_number = f"{batch_code}-{i:02d}"
        nieuwe_samples.append(
            {
                "intake_id": intake["id"],
                "sample_number": sample_number,
                "sample_index": i,
            }
        )

    samples = client.table("samples").insert(nieuwe_samples).execute().data
    samples.sort(key=lambda s: s["sample_index"])

    toon_voorstel()
    st.success(f"{len(samples)} staal/stalen ingelogd onder batch **{batch_code}**")
    st.write("Stalen: " + ", ".join(s["sample_number"] for s in samples))

    # Eén QR-code voor de hele batch (niet per staal): makkelijker om
    # dezelfde code meerdere keren af te drukken (bv. met een Dymo-printer)
    # dan om per staal een aparte code te moeten kopiëren.
    scan_url = f"{APP_BASE_URL}/Bekijk_Werkaanvraag?batch_id={intake['id']}"
    qr_img = qrcode.make(scan_url)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(buffer, width=150)
    with col2:
        st.write(f"**QR-code voor batch {batch_code}**")
        st.caption(f"Druk deze code {len(samples)}x af — één per staal.")
        st.code(scan_url, language=None)
        st.download_button(
            "Download QR-code (PNG)",
            data=buffer,
            file_name=f"{batch_code}.png",
            mime="image/png",
        )
