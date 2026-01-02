import psycopg2
import sys

conn = psycopg2.connect(
    host='db',
    port='5432',
    database='ast_db',
    user='ast_user',
    password='ast_password_2024'
)
cursor = conn.cursor()

print("--- DATA SOURCES (aggregation) ---")
cursor.execute("SELECT DISTINCT organism, antibiotic FROM organism_level_aggregation ORDER BY 1, 2")
aggs = cursor.fetchall()
for o, a in aggs:
    print(f"AGG: '{o}' | '{a}' (Len: {len(a)})")

print("\n--- TRAINED MODELS (performance) ---")
cursor.execute("SELECT DISTINCT organism, antibiotic FROM model_performance ORDER BY 1, 2")
models = cursor.fetchall()
for o, a in models:
    print(f"MOD: '{o}' | '{a}' (Len: {len(a)})")

print("\n--- COMPARISON ---")
model_set = set(models)
agg_set = set(aggs)

missing = agg_set - model_set
print(f"Missing models for {len(missing)} combinations (that exist in data)")
for o, a in list(missing)[:10]:
    print(f"MISSING: '{o}' + '{a}'")
