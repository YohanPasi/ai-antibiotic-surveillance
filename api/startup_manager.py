"""
startup_manager.py
Orchestrates creating default data/users if the database is empty.
"""
import os
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from data_processor.clean_and_load import clean_and_load_data
from data_processor.aggregate_weekly import aggregate_weekly_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup_manager")

DB_PARAMS = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'ast_db'),
    'user': os.getenv('DB_USER', 'ast_user'),
    'password': os.getenv('DB_PASSWORD', 'ast_password_2024')
}

class StartupManager:
    @staticmethod
    def ensure_startup_state():
        logger.info("🚀 Checking System Startup State...")
        
        try:
            conn = psycopg2.connect(**DB_PARAMS)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # 1. ENSURE USERS TABLE & ADMIN EXIST
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users');")
            users_exists = cursor.fetchone()[0]
            
            if not users_exists:
                logger.info("⚠️ 'users' table missing. running user schema script...")
                StartupManager.run_sql_file(cursor, '/docker-entrypoint-initdb.d/03_create_users_schema.sql')
                # Wait, the volume mapping for 03_ might not exist in docker-compose yet.
                # Let's read it from the local path since we are IN the container at /app
                StartupManager.run_local_sql_file(cursor, 'database/create_users_schema.sql')
            else:
                # Double check admin exists
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
                if cursor.fetchone()[0] == 0:
                    logger.info("⚠️ Admin user missing. Seeding default admin...")
                    # Insert default admin safely
                    cursor.execute("""
                        INSERT INTO users (username, email, password_hash, role)
                        VALUES ('admin', 'admin@hospital.lk', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6q.1/6.1/6.1/6.1/6.1', 'admin')
                    """)
                    logger.info("✓ Admin user seeded.")

            # 2. ENSURE DATA EXISTS
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ast_raw_data');")
            data_table_exists = cursor.fetchone()[0]

            if data_table_exists:
                cursor.execute("SELECT COUNT(*) FROM ast_raw_data")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    logger.warning("📉 Database exists but is EMPTY. Starting Data Seeding...")
                    success = clean_and_load_data()
                    if success:
                        logger.info("✓ Data Loading Complete. Starting Aggregation...")
                        aggregate_weekly_data()
                    else:
                        logger.error("❌ Data Loading Failed!")
                else:
                    logger.info(f"✓ Database Healthy ({count} records). Skipping Seeding.")
            else:
                logger.error("❌ ast_raw_data table does not exist! Check init scripts.")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Startup Check Failed: {e}")

    @staticmethod
    def run_local_sql_file(cursor, relative_path):
        """Reads a SQL file from /app/../Database location if possible or handles errors."""
        # In docker, we are in /app. database folder is at ../database usually? 
        # Check docker-compose: ./api:/app. Database is ./database. 
        # But wait, api container might not have access to ../database unless we mount it?
        # Checking docker-compose... 
        # Only ./api is mounted to /app. The database folder is NOT mounted to /app.
        # However, create_users_schema.sql is simple. I should probably just EMBED the SQL here 
        # or ask to mount the folder. embedding is safer for now to avoid docker-compose restart/changes.
        
        logger.info(f"Executing embedded user schema creation...")
        sql = """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO users (username, email, password_hash, role)
            SELECT 'admin', 'admin@hospital.lk', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6q.1/6.1/6.1/6.1/6.1', 'admin'
            WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');
        """
        cursor.execute(sql)
        logger.info("✓ Users table synced.")

if __name__ == "__main__":
    StartupManager.ensure_startup_state()
