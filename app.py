import os

import streamlit as st

st.set_page_config(page_title="QR Sample Tracker", page_icon="🧪")

with st.expander("Tijdelijke debug-info (APP_BASE_URL)"):
    st.write("'APP_BASE_URL' in st.secrets:", "APP_BASE_URL" in st.secrets)
    st.write("st.secrets waarde:", repr(st.secrets.get("APP_BASE_URL")))
    st.write("os.environ waarde:", repr(os.environ.get("APP_BASE_URL")))
    from db import APP_BASE_URL
    st.write("Uiteindelijke APP_BASE_URL:", repr(APP_BASE_URL))

st.title("🧪 QR Sample Tracker")
st.write(
    "Welkom! Gebruik het menu links om stalen in te loggen, een werkaanvraag "
    "aan te maken, een staal op te zoeken via QR-code, of het overzicht te bekijken."
)
st.info("MVP-testversie — enkel nepdata, geen echte bedrijfsgegevens.")
