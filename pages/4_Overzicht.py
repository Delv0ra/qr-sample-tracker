import base64
import datetime
import io

import pandas as pd
import qrcode
import streamlit as st

from db import APP_BASE_URL, get_client

st.set_page_config(page_title="Overzicht", page_icon="📋", layout="wide")
st.title("📋 Overzicht stalen")

client = get_client()


@st.cache_data
def qr_data_uri(batch_id: str) -> str:
    """De QR-afbeelding voor een batch verandert nooit (zelfde batch_id ->
    zelfde link), dus die hoeft maar één keer getekend te worden i.p.v. bij
    elke filter-aanpassing opnieuw."""
    scan_url = f"{APP_BASE_URL}/Bekijk_Werkaanvraag?batch_id={batch_id}"
    qr_img = qrcode.make(scan_url)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


@st.cache_data(ttl=30)
def haal_intakes() -> list[dict]:
    return (
        client.table("sample_intakes")
        .select("*")
        .order("created_at", desc=True)
        .execute()
        .data
    )


@st.cache_data(ttl=30)
def haal_samples_per_intake() -> list[dict]:
    return client.table("samples").select("id, intake_id").execute().data


@st.cache_data(ttl=30)
def haal_extra_velden() -> list[dict]:
    return (
        client.table("field_definitions")
        .select("*")
        .eq("entity", "sample_intake")
        .order("display_order")
        .execute()
        .data
    )


@st.cache_data(ttl=30)
def haal_categorieen() -> list[dict]:
    return (
        client.table("option_lists")
        .select("value")
        .eq("list_key", "category")
        .order("display_order")
        .execute()
        .data
    )


intakes = haal_intakes()

if not intakes:
    st.info("Er zijn nog geen stalen ingelogd.")
    st.stop()

samples = haal_samples_per_intake()
aantal_per_intake = pd.Series([s["intake_id"] for s in samples]).value_counts()

df = pd.DataFrame(intakes)
df["aantal_stalen"] = df["id"].map(aantal_per_intake).fillna(0).astype(int)

extra_velden = haal_extra_velden()
for veld in extra_velden:
    df[veld["field_key"]] = df["custom_fields"].apply(
        lambda cf, k=veld["field_key"]: (cf or {}).get(k, "")
    )

col1, col2 = st.columns(2)
col1.metric("🔄 Ongoing", int((df["status"] == "ongoing").sum()))
col2.metric("✅ Complete", int((df["status"] == "complete").sum()))

st.divider()

categorie_opties = haal_categorieen()

filter_col, cat_col, search_col = st.columns([1, 1, 2])
status_filter = filter_col.selectbox("Status", options=["Alle", "ongoing", "complete"])
category_filter = cat_col.selectbox(
    "Categorie", options=["Alle"] + [r["value"] for r in categorie_opties]
)
search_term = search_col.text_input("Zoeken (batch-nummer, klant of omschrijving)")

gefilterd = df.copy()

if status_filter != "Alle":
    gefilterd = gefilterd[gefilterd["status"] == status_filter]

if category_filter != "Alle":
    gefilterd = gefilterd[gefilterd["category"] == category_filter]

if search_term.strip():
    term = search_term.strip().lower()
    mask = (
        gefilterd["batch_code"].str.lower().str.contains(term, na=False)
        | gefilterd["customer"].str.lower().str.contains(term, na=False)
        | gefilterd["description"].str.lower().str.contains(term, na=False)
    )
    gefilterd = gefilterd[mask]

st.caption(f"{len(gefilterd)} van {len(df)} stalen-intakes getoond")

gefilterd = gefilterd.assign(qr=gefilterd["id"].apply(qr_data_uri))

vaste_kolommen = {
    "batch_code": "Batch-nummer",
    "customer": "Klant",
    "category": "Categorie",
    "status": "Status",
    "date_received": "Binnengekomen",
    "date_completed": "Voltooid",
    "aantal_stalen": "# samples",
    "description": "Omschrijving",
    "qr": "QR",
}
extra_kolommen = {veld["field_key"]: veld["label"] for veld in extra_velden}

weergave = gefilterd.rename(columns={**vaste_kolommen, **extra_kolommen})[
    [
        "Batch-nummer",
        "QR",
        "Klant",
        "Categorie",
        "Status",
        "Binnengekomen",
        "Voltooid",
        "# samples",
        *extra_kolommen.values(),
        "Omschrijving",
    ]
]

st.dataframe(
    weergave,
    width="stretch",
    hide_index=True,
    column_config={
        "QR": st.column_config.ImageColumn("QR", width="small", help="Klik om te vergroten"),
        "# samples": st.column_config.NumberColumn("# samples", width="small"),
        "Batch-nummer": st.column_config.TextColumn(width="small"),
        "Status": st.column_config.TextColumn(width="small"),
        "Categorie": st.column_config.TextColumn(width="small"),
        "Binnengekomen": st.column_config.TextColumn(width="small"),
        "Voltooid": st.column_config.TextColumn(width="small"),
    },
)

st.divider()
st.subheader("Status bijwerken")

intake_opties = {row["batch_code"]: row for row in intakes}
gekozen_batch = st.selectbox("Kies een batch", options=list(intake_opties.keys()))
huidige = intake_opties[gekozen_batch]

st.write(f"Huidige status: **{huidige['status']}**")

nieuwe_status = st.selectbox(
    "Nieuwe status",
    options=["ongoing", "complete"],
    index=["ongoing", "complete"].index(huidige["status"]),
    key="nieuwe_status",
)

if st.button("Status opslaan"):
    update_data = {"status": nieuwe_status}
    if nieuwe_status == "complete" and not huidige["date_completed"]:
        update_data["date_completed"] = datetime.date.today().isoformat()
    elif nieuwe_status == "ongoing":
        update_data["date_completed"] = None

    client.table("sample_intakes").update(update_data).eq("id", huidige["id"]).execute()
    haal_intakes.clear()
    st.success(f"Status van {gekozen_batch} bijgewerkt naar '{nieuwe_status}'.")
    st.rerun()
