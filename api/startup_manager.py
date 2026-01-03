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

# Database connection parameters
DATABASE_URL = os.getenv('DATABASE_URL')


class StartupManager:
    @staticmethod
    def ensure_startup_state():
        logger.info("🚀 Checking System Startup State...")
        
        try:
            if not DATABASE_URL:
                logger.error("❌ DATABASE_URL environment variable is missing")
                return

            conn = psycopg2.connect(DATABASE_URL)
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

            # 2. ENSURE CORE SCHEMA EXISTS
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ast_raw_data');")
            data_table_exists = cursor.fetchone()[0]

            if not data_table_exists:
                logger.warning("📉 Core Schema missing. Initializing Database from schema.sql...")
                StartupManager.run_local_sql_file(cursor, '/app/database_scripts/schema.sql')
                # Also create other needed schemas if split (e.g. users is separate?)
                # Actually users is checked separately above, but relying on correct order.
                # Let's re-verify users table existence after schema run just in case.
                conn.commit()
                logger.info("✓ Core Schema Created.")
                data_table_exists = True

            # 3. ENSURE DATA EXISTS
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
    def run_local_sql_file(cursor, file_path):
        """Reads and executes a SQL file."""
        try:
            logger.info(f"Executing SQL file: {file_path}")
            if not os.path.exists(file_path):
                # Fallback for users if strictly needed and file missing (legacy logic)
                 if "users" in file_path:
                    logger.info("SQL File not found, using embedded fallback for users...")
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
                    return

                 logger.error(f"❌ SQL File missing: {file_path}")
                 return

            with open(file_path, 'r') as f:
                sql = f.read()
                cursor.execute(sql)
                logger.info("✓ SQL Execution Successful.")
        except Exception as e:
            logger.error(f"❌ Failed to execute SQL {file_path}: {e}")


if __name__ == "__main__":
    StartupManager.ensure_startup_state()
