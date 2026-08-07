"""Klein testscript: controleert of de app met Supabase kan praten
en of de tabellen work_requests, sample_intakes en samples bestaan.

Uitvoeren met: .venv\\Scripts\\python.exe test_connection.py
"""
from db import get_client

client = get_client()

print("Verbinding maken met Supabase...")

for table in ("work_requests", "sample_intakes", "samples"):
    try:
        result = client.table(table).select("*").limit(1).execute()
        print(f"OK  - tabel '{table}' bestaat en is bereikbaar ({len(result.data)} rij(en) getoond)")
    except Exception as exc:
        print(f"FOUT - tabel '{table}': {exc}")
