import os
from sqlalchemy import create_engine, text
import urllib.parse

# Credentials from env output
# postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres
user = "postgres.zdhvyhijuriggezelyxq"
password = "Yohan&pasi80253327"
password_encoded = urllib.parse.quote_plus(password)
dbname = "postgres"

candidates = [
    {
        "name": "Candidate 1 (Region Direct)",
        "host": "aws-1-ap-northeast-2.supabase.com",
        "port": 5432
    },
    {
        "name": "Candidate 2 (Project Ref Direct)",
        "host": "db.zdhvyhijuriggezelyxq.supabase.co",
        "port": 5432
    },
    {
        "name": "Candidate 3 (Region Port 6543)",
        "host": "aws-1-ap-northeast-2.supabase.com",
        "port": 6543
    }
]

print("Testing connections...")

for c in candidates:
    url = f"postgresql://{user}:{password_encoded}@{c['host']}:{c['port']}/{dbname}?sslmode=require"
    print(f"\nTrying {c['name']}: {c['host']}:{c['port']}...")
    try:
        engine = create_engine(url, connect_args={'connect_timeout': 3})
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1")).scalar()
            print(f"✅ SUCCESS! Connected to {c['name']}")
            print(f"URL: {url}")
            exit(0) # Exit on first success to be fast
    except Exception as e:
        print(f"❌ Failed: {e}")
