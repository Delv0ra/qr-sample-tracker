"""Verbinding met de Supabase-database.

Leest de URL en API-key uit het .env-bestand (nooit hardcoded in code,
zodat we dit later veilig kunnen delen/verkopen zonder geheimen te lekken).
"""
import os
import ssl

import truststore

# Gebruik de certificaten van Windows zelf (i.p.v. Python's eigen lijst).
# Nodig omdat sommige antivirusprogramma's (bv. Norton) internetverkeer
# scannen met hun eigen certificaat, dat Windows wel vertrouwt maar
# Python standaard niet.
truststore.inject_into_ssl()

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8501")


def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)
