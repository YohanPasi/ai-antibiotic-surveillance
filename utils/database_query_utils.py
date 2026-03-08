"""
Advanced database query utilities for AMR surveillance system
Provides optimized queries and database interaction helpers
"""

import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor, execute_values
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manage database connection pool"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                database=self.config.get('database'),
                user=self.config.get('user'),
                password=self.config.get('password')
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        conn = self.connection_pool.getconn()
        try:
            yield conn
        finally:
            self.connection_pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """Get cursor with connection"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database transaction error: {e}")
                raise
            finally:
                cursor.close()
    
    def close_all_connections(self):
        """Close all connections in pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("All database connections closed")


class SampleDataQueries:
    """Queries for sample data operations"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def get_sample_by_id(self, sample_id: int) -> Optional[Dict]:
        """Get sample details by ID"""
        query = """
            SELECT 
                s.sample_id,
                s.patient_id,
                s.sample_date,
                s.sample_type,
                s.ward_id,
                w.ward_name,
                s.organism,
                s.collection_method
            FROM samples s
            LEFT JOIN wards w ON s.ward_id = w.ward_id
            WHERE s.sample_id = %s
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (sample_id,))
            return cursor.fetchone()
    
    def get_samples_by_date_range(self, start_date: datetime, 
                                  end_date: datetime,
                                  ward_id: Optional[int] = None) -> List[Dict]:
        """Get samples within date range"""
        query = """
            SELECT 
                s.sample_id,
                s.patient_id,
                s.sample_date,
                s.sample_type,
                s.organism,
                w.ward_name,
                COUNT(st.susceptibility_id) as antibiotic_count
            FROM samples s
            LEFT JOIN wards w ON s.ward_id = w.ward_id
            LEFT JOIN susceptibility_tests st ON s.sample_id = st.sample_id
            WHERE s.sample_date BETWEEN %s AND %s
        """
        
        params = [start_date, end_date]
        
        if ward_id:
            query += " AND s.ward_id = %s"
            params.append(ward_id)
        
        query += " GROUP BY s.sample_id, s.patient_id, s.sample_date, s.sample_type, s.organism, w.ward_name"
        query += " ORDER BY s.sample_date DESC"
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_samples_by_organism(self, organism: str, 
                               limit: int = 100) -> List[Dict]:
        """Get samples for specific organism"""
        query = """
            SELECT 
                s.*,
                w.ward_name,
                p.age,
                p.gender
            FROM samples s
            LEFT JOIN wards w ON s.ward_id = w.ward_id
            LEFT JOIN patients p ON s.patient_id = p.patient_id
            WHERE s.organism ILIKE %s
            ORDER BY s.sample_date DESC
            LIMIT %s
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (f'%{organism}%', limit))
            return cursor.fetchall()
    
    def insert_sample(self, sample_data: Dict) -> int:
        """Insert new sample record"""
        query = """
            INSERT INTO samples (
                patient_id, sample_date, sample_type, ward_id,
                organism, collection_method, created_at
            ) VALUES (
                %(patient_id)s, %(sample_date)s, %(sample_type)s, %(ward_id)s,
                %(organism)s, %(collection_method)s, NOW()
            )
            RETURNING sample_id
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, sample_data)
            result = cursor.fetchone()
            return result['sample_id'] if result else None
    
    def update_sample(self, sample_id: int, update_data: Dict) -> bool:
        """Update sample record"""
        set_clause = ', '.join([f"{key} = %({key})s" for key in update_data.keys()])
        query = f"""
            UPDATE samples
            SET {set_clause}, updated_at = NOW()
            WHERE sample_id = %(sample_id)s
        """
        
        update_data['sample_id'] = sample_id
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, update_data)
            return cursor.rowcount > 0
    
    def delete_sample(self, sample_id: int) -> bool:
        """Delete sample record"""
        query = "DELETE FROM samples WHERE sample_id = %s"
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (sample_id,))
            return cursor.rowcount > 0


class SusceptibilityQueries:
    """Queries for antibiotic susceptibility data"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def get_susceptibility_by_sample(self, sample_id: int) -> List[Dict]:
        """Get all susceptibility tests for a sample"""
        query = """
            SELECT 
                st.susceptibility_id,
                st.antibiotic,
                st.result,
                st.mic_value,
                st.tested_date
            FROM susceptibility_tests st
            WHERE st.sample_id = %s
            ORDER BY st.antibiotic
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (sample_id,))
            return cursor.fetchall()
    
    def get_resistance_rate(self, organism: str, antibiotic: str,
                           start_date: datetime, end_date: datetime) -> Dict:
        """Calculate resistance rate for organism-antibiotic pair"""
        query = """
            SELECT 
                COUNT(*) as total_tests,
                SUM(CASE WHEN st.result = 'R' THEN 1 ELSE 0 END) as resistant_count,
                SUM(CASE WHEN st.result = 'S' THEN 1 ELSE 0 END) as susceptible_count,
                SUM(CASE WHEN st.result = 'I' THEN 1 ELSE 0 END) as intermediate_count
            FROM susceptibility_tests st
            JOIN samples s ON st.sample_id = s.sample_id
            WHERE s.organism ILIKE %s
            AND st.antibiotic ILIKE %s
            AND s.sample_date BETWEEN %s AND %s
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (f'%{organism}%', f'%{antibiotic}%', start_date, end_date))
            result = cursor.fetchone()
            
            if result and result['total_tests'] > 0:
                return {
                    'total_tests': result['total_tests'],
                    'resistant_count': result['resistant_count'],
                    'susceptible_count': result['susceptible_count'],
                    'intermediate_count': result['intermediate_count'],
                    'resistance_rate': (result['resistant_count'] / result['total_tests']) * 100
                }
            
            return {'total_tests': 0, 'resistance_rate': 0}
    
    def insert_susceptibility_test(self, test_data: Dict) -> int:
        """Insert susceptibility test result"""
        query = """
            INSERT INTO susceptibility_tests (
                sample_id, antibiotic, result, mic_value, tested_date
            ) VALUES (
                %(sample_id)s, %(antibiotic)s, %(result)s, %(mic_value)s, %(tested_date)s
            )
            RETURNING susceptibility_id
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, test_data)
            result = cursor.fetchone()
            return result['susceptibility_id'] if result else None
    
    def bulk_insert_susceptibility_tests(self, tests_data: List[Dict]) -> int:
        """Bulk insert susceptibility tests"""
        query = """
            INSERT INTO susceptibility_tests (
                sample_id, antibiotic, result, mic_value, tested_date
            ) VALUES %s
        """
        
        values = [
            (t['sample_id'], t['antibiotic'], t['result'], 
             t.get('mic_value'), t['tested_date'])
            for t in tests_data
        ]
        
        with self.db.get_cursor() as cursor:
            execute_values(cursor, query, values)
            return cursor.rowcount


class PatientQueries:
    """Queries for patient data"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def get_patient_by_id(self, patient_id: int) -> Optional[Dict]:
        """Get patient details"""
        query = """
            SELECT 
                patient_id,
                age,
                gender,
                admission_date,
                discharge_date,
                diagnosis,
                prior_antibiotics
            FROM patients
            WHERE patient_id = %s
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (patient_id,))
            return cursor.fetchone()
    
    def get_patient_samples(self, patient_id: int) -> List[Dict]:
        """Get all samples for a patient"""
        query = """
            SELECT 
                s.sample_id,
                s.sample_date,
                s.sample_type,
                s.organism,
                w.ward_name
            FROM samples s
            LEFT JOIN wards w ON s.ward_id = w.ward_id
            WHERE s.patient_id = %s
            ORDER BY s.sample_date DESC
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (patient_id,))
            return cursor.fetchall()
    
    def get_patient_antibiotic_history(self, patient_id: int) -> List[Dict]:
        """Get patient's prior antibiotic exposure"""
        query = """
            SELECT 
                p.prior_antibiotics,
                p.admission_date,
                ARRAY_AGG(DISTINCT st.antibiotic) as tested_antibiotics
            FROM patients p
            LEFT JOIN samples s ON p.patient_id = s.patient_id
            LEFT JOIN susceptibility_tests st ON s.sample_id = st.sample_id
            WHERE p.patient_id = %s
            GROUP BY p.patient_id, p.prior_antibiotics, p.admission_date
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (patient_id,))
            return cursor.fetchall()


class WardQueries:
    """Queries for ward-level data"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def get_ward_statistics(self, ward_id: int, 
                           start_date: datetime,
                           end_date: datetime) -> Dict:
        """Get ward statistics for date range"""
        query = """
            SELECT 
                w.ward_id,
                w.ward_name,
                COUNT(DISTINCT s.sample_id) as total_samples,
                COUNT(DISTINCT s.patient_id) as total_patients,
                COUNT(DISTINCT CASE WHEN st.result = 'R' THEN s.sample_id END) as resistant_samples
            FROM wards w
            LEFT JOIN samples s ON w.ward_id = s.ward_id
            LEFT JOIN susceptibility_tests st ON s.sample_id = st.sample_id
            WHERE w.ward_id = %s
            AND s.sample_date BETWEEN %s AND %s
            GROUP BY w.ward_id, w.ward_name
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (ward_id, start_date, end_date))
            return cursor.fetchone()
    
    def get_ward_organism_distribution(self, ward_id: int,
                                      days: int = 30) -> List[Dict]:
        """Get organism distribution in ward"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = """
            SELECT 
                s.organism,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM samples s
            WHERE s.ward_id = %s
            AND s.sample_date BETWEEN %s AND %s
            GROUP BY s.organism
            ORDER BY count DESC
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (ward_id, start_date, end_date))
            return cursor.fetchall()
    
    def detect_ward_outbreak(self, ward_id: int, threshold: float = 2.0) -> List[Dict]:
        """Detect potential outbreaks in ward"""
        query = """
            WITH weekly_counts AS (
                SELECT 
                    DATE_TRUNC('week', sample_date) as week,
                    organism,
                    COUNT(*) as count
                FROM samples
                WHERE ward_id = %s
                AND sample_date >= NOW() - INTERVAL '12 weeks'
                GROUP BY DATE_TRUNC('week', sample_date), organism
            ),
            stats AS (
                SELECT 
                    organism,
                    AVG(count) as avg_count,
                    STDDEV(count) as stddev_count
                FROM weekly_counts
                GROUP BY organism
            )
            SELECT 
                wc.week,
                wc.organism,
                wc.count,
                s.avg_count,
                s.stddev_count,
                (wc.count - s.avg_count) / NULLIF(s.stddev_count, 0) as z_score
            FROM weekly_counts wc
            JOIN stats s ON wc.organism = s.organism
            WHERE (wc.count - s.avg_count) / NULLIF(s.stddev_count, 0) > %s
            ORDER BY wc.week DESC, z_score DESC
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (ward_id, threshold))
            return cursor.fetchall()


class AnalyticsQueries:
    """Complex analytical queries"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def get_resistance_trends(self, organism: str, 
                             months: int = 12) -> pd.DataFrame:
        """Get resistance trends over time"""
        query = """
            SELECT 
                DATE_TRUNC('month', s.sample_date) as month,
                st.antibiotic,
                COUNT(*) as total_tests,
                SUM(CASE WHEN st.result = 'R' THEN 1 ELSE 0 END) as resistant_count,
                ROUND(100.0 * SUM(CASE WHEN st.result = 'R' THEN 1 ELSE 0 END) / COUNT(*), 2) as resistance_rate
            FROM samples s
            JOIN susceptibility_tests st ON s.sample_id = st.sample_id
            WHERE s.organism ILIKE %s
            AND s.sample_date >= NOW() - INTERVAL '%s months'
            GROUP BY DATE_TRUNC('month', s.sample_date), st.antibiotic
            ORDER BY month DESC, st.antibiotic
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (f'%{organism}%', months))
            results = cursor.fetchall()
            return pd.DataFrame(results)
    
    def get_cross_resistance_matrix(self, organism: str) -> pd.DataFrame:
        """Get cross-resistance patterns"""
        query = """
            WITH sample_resistance AS (
                SELECT 
                    s.sample_id,
                    st.antibiotic,
                    CASE WHEN st.result = 'R' THEN 1 ELSE 0 END as is_resistant
                FROM samples s
                JOIN susceptibility_tests st ON s.sample_id = st.sample_id
                WHERE s.organism ILIKE %s
            )
            SELECT 
                sr1.antibiotic as antibiotic1,
                sr2.antibiotic as antibiotic2,
                COUNT(*) as total_samples,
                SUM(sr1.is_resistant * sr2.is_resistant) as both_resistant,
                ROUND(100.0 * SUM(sr1.is_resistant * sr2.is_resistant) / COUNT(*), 2) as correlation
            FROM sample_resistance sr1
            JOIN sample_resistance sr2 ON sr1.sample_id = sr2.sample_id
            WHERE sr1.antibiotic < sr2.antibiotic
            GROUP BY sr1.antibiotic, sr2.antibiotic
            HAVING COUNT(*) >= 10
            ORDER BY correlation DESC
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (f'%{organism}%',))
            results = cursor.fetchall()
            return pd.DataFrame(results)
    
    def get_prediction_performance_metrics(self, model_name: str,
                                          days: int = 30) -> Dict:
        """Get model prediction performance"""
        query = """
            SELECT 
                model_name,
                COUNT(*) as total_predictions,
                SUM(CASE WHEN predicted_result = actual_result THEN 1 ELSE 0 END) as correct_predictions,
                ROUND(100.0 * SUM(CASE WHEN predicted_result = actual_result THEN 1 ELSE 0 END) / COUNT(*), 2) as accuracy,
                AVG(confidence_score) as avg_confidence,
                AVG(prediction_time_ms) as avg_prediction_time
            FROM prediction_log
            WHERE model_name = %s
            AND prediction_date >= NOW() - INTERVAL '%s days'
            GROUP BY model_name
        """
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (model_name, days))
            return cursor.fetchone()


def main():
    """Example usage"""
    config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'sentinel_amr',
        'user': 'postgres',
        'password': 'password'
    }
    
    try:
        db = DatabaseConnection(config)
        
        # Example: Get sample queries
        sample_queries = SampleDataQueries(db)
        samples = sample_queries.get_samples_by_date_range(
            datetime.now() - timedelta(days=7),
            datetime.now()
        )
        print(f"Found {len(samples)} samples in the last 7 days")
        
        # Close connections
        db.close_all_connections()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == '__main__':
    main()
