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


def qr_data_uri(batch_id: str) -> str:
    scan_url = f"{APP_BASE_URL}/Bekijk_Werkaanvraag?batch_id={batch_id}"
    qr_img = qrcode.make(scan_url)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


intakes = (
    client.table("sample_intakes")
    .select("*")
    .order("created_at", desc=True)
    .execute()
    .data
)

if not intakes:
    st.info("Er zijn nog geen stalen ingelogd.")
    st.stop()

samples = client.table("samples").select("id, intake_id").execute().data
aantal_per_intake = pd.Series([s["intake_id"] for s in samples]).value_counts()

df = pd.DataFrame(intakes)
df["aantal_stalen"] = df["id"].map(aantal_per_intake).fillna(0).astype(int)

col1, col2 = st.columns(2)
col1.metric("🔄 Ongoing", int((df["status"] == "ongoing").sum()))
col2.metric("✅ Complete", int((df["status"] == "complete").sum()))

st.divider()

filter_col, cat_col, search_col = st.columns([1, 1, 2])
status_filter = filter_col.selectbox("Status", options=["Alle", "ongoing", "complete"])
category_filter = cat_col.selectbox(
    "Categorie", options=["Alle", "quality control", "complaint", "process monitoring"]
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

weergave = gefilterd.rename(
    columns={
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
)[
    [
        "Batch-nummer",
        "QR",
        "Klant",
        "Categorie",
        "Status",
        "Binnengekomen",
        "Voltooid",
        "# samples",
        "Omschrijving",
    ]
]

st.dataframe(
    weergave,
    use_container_width=True,
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
    st.success(f"Status van {gekozen_batch} bijgewerkt naar '{nieuwe_status}'.")
    st.rerun()
