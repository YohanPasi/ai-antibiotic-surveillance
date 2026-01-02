import psycopg2
import csv
import os

DB_PARAMS = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'ast_db'),
    'user': os.getenv('DB_USER', 'ast_user'),
    'password': os.getenv('DB_PASSWORD', 'ast_password_2024')
}

OUTPUT_FILE = "/app/training_data.csv"

def export_data():
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    # We want a sequence of S% values ordered by time, grouped by combo
    # This allows the sliding window to work across targets as "episodes" if done right,
    # but for Stage D demo we follow the existing training script's logic of one big sequence.
    cursor.execute("""
        SELECT susceptibility_percent 
        FROM ast_weekly_aggregated 
        WHERE susceptibility_percent IS NOT NULL 
        ORDER BY ward, organism, antibiotic, week_start_date
    """)
    
    rows = cursor.fetchall()
    
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['susceptibility_percent'])
        writer.writerows(rows)
        
    print(f"Exported {len(rows)} records to {OUTPUT_FILE}")
    conn.close()

if __name__ == "__main__":
    export_data()
