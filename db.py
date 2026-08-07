"""Verbinding met de Supabase-database.

Leest instellingen uit het .env-bestand bij lokaal draaien, of uit Streamlit
Cloud's "Secrets" bij online draaien (nooit hardcoded in code, zodat we dit
later veilig kunnen delen/verkopen zonder geheimen te lekken).
"""
import os
import ssl

import streamlit as st
import truststore

# Gebruik de certificaten van Windows zelf (i.p.v. Python's eigen lijst).
# Nodig omdat sommige antivirusprogramma's (bv. Norton) internetverkeer
# scannen met hun eigen certificaat, dat Windows wel vertrouwt maar
# Python standaard niet.
truststore.inject_into_ssl()

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


def _get_setting(key: str, default: str | None = None) -> str:
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    if default is not None:
        return os.environ.get(key, default)
    return os.environ[key]


SUPABASE_URL = _get_setting("SUPABASE_URL")
SUPABASE_KEY = _get_setting("SUPABASE_KEY")
APP_BASE_URL = _get_setting("APP_BASE_URL", "http://localhost:8501")


def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)
