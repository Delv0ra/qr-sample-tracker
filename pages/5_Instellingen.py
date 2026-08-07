import re

import streamlit as st

from db import get_client


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")

st.set_page_config(page_title="Instellingen", page_icon="⚙️")
st.title("⚙️ Instellingen")

# Tijdelijk, hardcoded wachtwoord — enkel bedoeld voor deze testfase (geen
# echte/vertrouwelijke data). Vervangen door echt gebruikersbeheer voor er
# ooit gevoelige data bij komt.
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

client = get_client()

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if not st.session_state.is_admin:
    st.info("Deze pagina is enkel voor de beheerder (admin).")
    with st.form("admin_login"):
        username = st.text_input("Gebruikersnaam")
        password = st.text_input("Wachtwoord", type="password")
        submitted = st.form_submit_button("Inloggen")

    if submitted:
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.error("Ongeldige gebruikersnaam of wachtwoord.")
    st.stop()

col1, col2 = st.columns([4, 1])
with col1:
    st.success("Ingelogd als beheerder.")
with col2:
    if st.button("Uitloggen"):
        st.session_state.is_admin = False
        st.rerun()

st.divider()
st.subheader("Keuzelijsten beheren")
st.caption(
    "Categorieën die je kan kiezen bij het inloggen van stalen. Voeg toe of "
    "verwijder naar wens."
)

LIST_KEY = "category"

huidige_opties = (
    client.table("option_lists")
    .select("*")
    .eq("list_key", LIST_KEY)
    .order("display_order")
    .execute()
    .data
)

if not huidige_opties:
    st.warning("Er zijn nog geen categorieën. Voeg er hieronder minstens één toe.")

for optie in huidige_opties:
    opt_col1, opt_col2 = st.columns([4, 1])
    opt_col1.write(optie["value"])
    if opt_col2.button("Verwijderen", key=f"del_opt_{optie['id']}"):
        client.table("option_lists").delete().eq("id", optie["id"]).execute()
        st.rerun()

with st.form("nieuwe_optie", clear_on_submit=True):
    nieuwe_waarde = st.text_input("Nieuwe categorie toevoegen")
    toegevoegd = st.form_submit_button("Toevoegen")

if toegevoegd:
    if not nieuwe_waarde.strip():
        st.error("Vul een waarde in.")
    else:
        max_order = max([o["display_order"] for o in huidige_opties], default=0)
        bestaat_al = any(
            o["value"].strip().lower() == nieuwe_waarde.strip().lower() for o in huidige_opties
        )
        if bestaat_al:
            st.error("Deze categorie bestaat al.")
        else:
            client.table("option_lists").insert(
                {
                    "list_key": LIST_KEY,
                    "value": nieuwe_waarde.strip(),
                    "display_order": max_order + 1,
                }
            ).execute()
            st.success(f"'{nieuwe_waarde.strip()}' toegevoegd.")
            st.rerun()

st.divider()
st.subheader("Extra velden beheren")
st.caption(
    "Voeg eigen extra velden toe aan de formulieren. Ze verschijnen automatisch "
    "in het formulier, het overzicht, en bij het opzoeken."
)

ENTITY_LABELS = {"sample_intake": "Stalen inloggen", "work_request": "Werkaanvraag aanmaken"}
FIELD_TYPES = {
    "text": "Tekst",
    "number": "Getal",
    "date": "Datum",
    "boolean": "Ja/nee",
    "select": "Keuzelijst",
}

gekozen_entity = st.selectbox(
    "Voor welk formulier?",
    options=list(ENTITY_LABELS.keys()),
    format_func=lambda k: ENTITY_LABELS[k],
)

velden = (
    client.table("field_definitions")
    .select("*")
    .eq("entity", gekozen_entity)
    .order("display_order")
    .execute()
    .data
)

if not velden:
    st.caption("Nog geen extra velden voor dit formulier.")

for veld in velden:
    v_col1, v_col2, v_col3 = st.columns([3, 3, 1])
    v_col1.write(f"**{veld['label']}**")
    type_label = FIELD_TYPES.get(veld["field_type"], veld["field_type"])
    extra = f" ({', '.join(veld['options'])})" if veld.get("options") else ""
    verplicht_label = " — verplicht" if veld["required"] else ""
    v_col2.write(f"{type_label}{extra}{verplicht_label}")
    if v_col3.button("Verwijderen", key=f"del_field_{veld['id']}"):
        client.table("field_definitions").delete().eq("id", veld["id"]).execute()
        st.rerun()

with st.form(f"nieuw_veld_{gekozen_entity}", clear_on_submit=True):
    veld_label = st.text_input("Naam van het nieuwe veld")
    veld_type = st.selectbox(
        "Type", options=list(FIELD_TYPES.keys()), format_func=lambda k: FIELD_TYPES[k]
    )
    veld_opties_tekst = st.text_area(
        "Keuzeopties (één per lijn — enkel nodig bij type 'Keuzelijst')"
    )
    veld_verplicht = st.checkbox("Verplicht veld")
    veld_toegevoegd = st.form_submit_button("Veld toevoegen")

if veld_toegevoegd:
    if not veld_label.strip():
        st.error("Vul een naam in.")
    else:
        field_key = slugify(veld_label)
        bestaat_al = any(v["field_key"] == field_key for v in velden)
        if not field_key:
            st.error("Deze naam levert geen geldige veld-sleutel op, kies een andere naam.")
        elif bestaat_al:
            st.error("Er bestaat al een (bijna) gelijknamig veld voor dit formulier.")
        elif veld_type == "select" and not veld_opties_tekst.strip():
            st.error("Vul minstens één keuzeoptie in voor een keuzelijst-veld.")
        else:
            opties_lijst = None
            if veld_type == "select":
                opties_lijst = [o.strip() for o in veld_opties_tekst.splitlines() if o.strip()]
            max_order = max([v["display_order"] for v in velden], default=0)
            client.table("field_definitions").insert(
                {
                    "entity": gekozen_entity,
                    "field_key": field_key,
                    "label": veld_label.strip(),
                    "field_type": veld_type,
                    "options": opties_lijst,
                    "required": veld_verplicht,
                    "display_order": max_order + 1,
                }
            ).execute()
            st.success(f"Veld '{veld_label.strip()}' toegevoegd.")
            st.rerun()
