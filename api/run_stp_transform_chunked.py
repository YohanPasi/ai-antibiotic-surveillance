"""
STP Stage 1: Chunked Wide-to-Long Transformation (Fast Path)
============================================================
Uses raw psycopg2.extras.execute_values for maximum throughput via Session Mode pooler.
"""
import sys
import json
import logging
import urllib.parse
import psycopg2
from psycopg2.extras import execute_values

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Credentials
# Using Session Mode connection (port 6543) via pooler hostname to bypass IPv6 blocks on direct connection
DB_USER = "postgres.zdhvyhijuriggezelyxq"
DB_PASS = "Yohan&pasi80253327"
DB_HOST = "aws-1-ap-northeast-2.pooler.supabase.com" 
DB_PORT = "6543" 
DB_NAME = "postgres"

def transform_chunk(dataset_version, chunk_start, chunk_size=500):
    """Transform and insert chunk using raw psycopg2."""
    
    # Establish raw connection (bypassing SQLAlchemy Session overhead)
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        sslmode='require'
    )
    conn.autocommit = False # Transaction control
    
    try:
        with conn.cursor() as cur:
            # 1. Fetch Data
            cur.execute(f"""
                SELECT isolate_id, sample_date, organism, ward, sample_type, antibiotic_results
                FROM stp_raw_wide
                WHERE dataset_version = %s
                ORDER BY isolate_id
                LIMIT %s OFFSET %s
            """, (dataset_version, chunk_size, chunk_start))
            
            rows = cur.fetchall()
            long_batch = []
            
            for row in rows:
                isolate_id, sample_date, organism, ward, sample_type, antibiotic_results = row
                
                # Parse JSON
                ab_dict = json.loads(antibiotic_results) if isinstance(antibiotic_results, str) else antibiotic_results
                if not ab_dict: continue

                for antibiotic, ast_result in ab_dict.items():
                    if ast_result and ast_result != 'NA':
                        long_batch.append((
                            isolate_id, sample_date, organism, ward, sample_type,
                            antibiotic, ast_result, dataset_version
                        ))
            
            # 2. Bulk Insert (Fast)
            if long_batch:
                execute_values(
                    cur,
                    """
                    INSERT INTO stp_canonical_long (
                        isolate_id, sample_date, organism, ward, sample_type,
                        antibiotic, ast_result, dataset_version
                    ) VALUES %s
                    """,
                    long_batch
                )
        
        conn.commit()
        return len(long_batch)
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# Main Execution
print("=" * 70)
print("STP TRANSFORMATION: TURBO MODE (PSYCOPG2 RAW)")
print("=" * 70)

dataset_version = 'v1.0.0'
chunk_size = 500
total_rows = 12000
total_ast_tests = 0

# STEP 0: Clear existing data for this version (User Request)
print(f"🧹 Clearing existing data for version {dataset_version}...")
conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    port=DB_PORT,
    sslmode='require'
)
conn.autocommit = True
try:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM stp_canonical_long WHERE dataset_version = %s", (dataset_version,))
        print("✅ Data cleared.")
except Exception as e:
    print(f"❌ Failed to clear data: {e}")
    exit(1)
finally:
    conn.close()

for chunk_start in range(0, total_rows, chunk_size):
    chunk_num = (chunk_start // chunk_size) + 1
    logger.info(f"[Chunk {chunk_num}] Rows {chunk_start}-{chunk_start+chunk_size-1}")
    
    try:
        tests = transform_chunk(dataset_version, chunk_start, chunk_size)
        logger.info(f"  ✓ Created {tests} AST tests")
        total_ast_tests += tests
    except Exception as e:
        logger.error(f"  ❌ Chunk failed: {e}")
        # Retry? Or fail? Fail fast for diagnosis.
        raise

print("\n" + "=" * 70)
print("✅ TRANSFORMATION COMPLETE")
print(f"Total AST tests created: {total_ast_tests:,}")
print("=" * 70)
