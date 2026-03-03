"""
Phase 2.5 Migration — Master Data Panel Tables
================================================
Creates 3 new tables:
  - organisms              : canonical organism master list
  - antibiotics            : canonical antibiotic master list (with short codes)
  - organism_antibiotic_panel : organism ↔ antibiotic mapping (soft-delete via is_active)

Seeds all 5 surveillance organisms with their clinically validated antibiotic panels.

Safe to re-run: uses CREATE TABLE IF NOT EXISTS + INSERT ... ON CONFLICT DO NOTHING.
"""

import os
import psycopg2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

# ---------------------------------------------------------------------------
# Canonical seed data — normalized names, no brackets, title-case
# short_code from CLSI/EUCAST standard abbreviations
# ---------------------------------------------------------------------------
ORGANISMS = [
    ('Pseudomonas aeruginosa',  'NonFermenters'),
    ('Acinetobacter baumannii', 'NonFermenters'),
    ('Staphylococcus aureus',   'MRSA'),
    ('Escherichia coli',        'ESBL'),
    ('Klebsiella pneumoniae',   'ESBL'),
]

ANTIBIOTICS = [
    # name                         short_code
    ('Meropenem',                  'MEM'),
    ('Imipenem',                   'IPM'),
    ('Ceftazidime',                'CAZ'),
    ('Cefepime',                   'FEP'),
    ('Amikacin',                   'AK'),
    ('Tobramycin',                 'TOB'),
    ('Colistin',                   'COL'),
    ('Piperacillin-Tazobactam',    'TZP'),
    ('Ciprofloxacin',              'CIP'),
    ('Ampicillin-Sulbactam',       'SAM'),
    # MRSA panel
    ('Cefoxitin',                  'FOX'),
    ('Vancomycin',                 'VA'),
    ('Clindamycin',                'DA'),
    ('Erythromycin',               'E'),
    ('Linezolid',                  'LZD'),
    # ESBL panel
    ('Ampicillin',                 'AMP'),
    ('Cefuroxime',                 'CXM'),
    ('Ceftriaxone',                'CRO'),
    ('Gentamicin',                 'CN'),
    ('Amoxicillin-Clavulanate',    'AMC'),
]

# organism name → [antibiotic names]
PANELS = {
    'Pseudomonas aeruginosa':  [
        'Meropenem', 'Imipenem', 'Ceftazidime', 'Cefepime',
        'Amikacin', 'Tobramycin', 'Colistin',
        'Piperacillin-Tazobactam', 'Ciprofloxacin',
    ],
    'Acinetobacter baumannii': [
        'Meropenem', 'Imipenem', 'Ceftazidime', 'Cefepime',
        'Amikacin', 'Tobramycin', 'Colistin', 'Ampicillin-Sulbactam',
    ],
    'Staphylococcus aureus': [
        'Cefoxitin', 'Vancomycin', 'Clindamycin', 'Erythromycin', 'Linezolid',
    ],
    'Escherichia coli': [
        'Ampicillin', 'Cefuroxime', 'Ceftriaxone', 'Gentamicin', 'Imipenem',
    ],
    'Klebsiella pneumoniae': [
        'Amoxicillin-Clavulanate', 'Ceftazidime', 'Ciprofloxacin', 'Meropenem',
    ],
}


def run_migration():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable not set.")

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        logger.info("=" * 60)
        logger.info("Phase 2.5 — Panel Migration Starting")
        logger.info("=" * 60)

        # ── 1. Create tables ───────────────────────────────────────────
        logger.info("Creating tables if not exist...")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS organisms (
                id         SERIAL PRIMARY KEY,
                name       VARCHAR(200) UNIQUE NOT NULL,
                group_name VARCHAR(100) NOT NULL DEFAULT 'General',
                is_active  BOOLEAN DEFAULT TRUE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS antibiotics (
                id         SERIAL PRIMARY KEY,
                name       VARCHAR(200) UNIQUE NOT NULL,
                short_code VARCHAR(50),
                is_active  BOOLEAN DEFAULT TRUE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS organism_antibiotic_panel (
                organism_id   INTEGER REFERENCES organisms(id)   ON DELETE CASCADE,
                antibiotic_id INTEGER REFERENCES antibiotics(id) ON DELETE CASCADE,
                is_active     BOOLEAN DEFAULT TRUE,
                PRIMARY KEY (organism_id, antibiotic_id)
            );
        """)

        # Performance indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_oap_org
                ON organism_antibiotic_panel(organism_id);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_oap_abx
                ON organism_antibiotic_panel(antibiotic_id);
        """)

        logger.info("✅ Tables and indexes ready.")

        # ── 2. Seed organisms ──────────────────────────────────────────
        logger.info("Seeding organisms...")
        for name, group in ORGANISMS:
            cur.execute("""
                INSERT INTO organisms (name, group_name)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING;
            """, (name, group))
        logger.info(f"  {len(ORGANISMS)} organisms processed.")

        # ── 3. Seed antibiotics ────────────────────────────────────────
        logger.info("Seeding antibiotics...")
        for name, short_code in ANTIBIOTICS:
            cur.execute("""
                INSERT INTO antibiotics (name, short_code)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING;
            """, (name, short_code))
        logger.info(f"  {len(ANTIBIOTICS)} antibiotics processed.")

        # ── 4. Seed panel mappings ─────────────────────────────────────
        logger.info("Seeding organism-antibiotic panel mappings...")
        mapping_count = 0
        for org_name, abx_list in PANELS.items():
            # Get organism id
            cur.execute("SELECT id FROM organisms WHERE name = %s", (org_name,))
            org_row = cur.fetchone()
            if not org_row:
                logger.warning(f"  Organism not found: {org_name} — skipping panel")
                continue
            org_id = org_row[0]

            for abx_name in abx_list:
                cur.execute("SELECT id FROM antibiotics WHERE name = %s", (abx_name,))
                abx_row = cur.fetchone()
                if not abx_row:
                    logger.warning(f"  Antibiotic not found: {abx_name} — skipping")
                    continue
                abx_id = abx_row[0]

                cur.execute("""
                    INSERT INTO organism_antibiotic_panel (organism_id, antibiotic_id, is_active)
                    VALUES (%s, %s, TRUE)
                    ON CONFLICT (organism_id, antibiotic_id) DO NOTHING;
                """, (org_id, abx_id))
                mapping_count += 1

        logger.info(f"  {mapping_count} panel mappings processed.")

        conn.commit()
        logger.info("=" * 60)
        logger.info("✅ Phase 2.5 Migration Complete.")
        logger.info("=" * 60)

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Migration failed, rolling back: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    run_migration()
