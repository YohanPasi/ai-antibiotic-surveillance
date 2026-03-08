"""
apply_beta_lactam_schema.py
===========================
Step 1 database setup script for the Beta-Lactam Resistance Spectrum
Prediction module.

Runs in two modes:
  --fresh   Create all new tables from scratch (for new environments).
  --migrate Alter existing ESBL tables (for environments with live data).

Usage:
    python apply_beta_lactam_schema.py --fresh
    python apply_beta_lactam_schema.py --migrate
"""

import os
import sys
import argparse
from sqlalchemy import create_engine, text

# ── Database connection ────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set.")

engine = create_engine(DATABASE_URL, echo=False)

# ── Paths to SQL files ─────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Fallback to database_scripts if database folder doesn't exist (Docker volume mapping)
DATABASE_DIR = os.path.join(BASE_DIR, "database_scripts")
if not os.path.exists(DATABASE_DIR):
    DATABASE_DIR = os.path.join(os.path.dirname(BASE_DIR), "database")

FRESH_SCRIPTS = [
    "create_beta_lactam_encounters.sql",
    "create_beta_lactam_lab_results.sql",
    "create_beta_lactam_audit_logs.sql",
]

MIGRATION_SCRIPT = "migrate_to_beta_lactam_spectrum.sql"


def run_sql_file(path: str, conn):
    """Read and execute a SQL file, skipping blank lines and comments."""
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Execute as a single block (handles multi-statement DDL + DML)
    conn.execute(text(sql))
    print(f"  ✅ Applied: {os.path.basename(path)}")


def apply_fresh():
    """Create all new beta-lactam tables from scratch."""
    print("\n🚀 Mode: FRESH — Creating new beta-lactam tables...\n")
    with engine.begin() as conn:
        for script in FRESH_SCRIPTS:
            path = os.path.join(DATABASE_DIR, script)
            if not os.path.exists(path):
                print(f"  ⚠️  File not found, skipping: {script}")
                continue
            run_sql_file(path, conn)
    print("\n✅ All beta-lactam tables created successfully.\n")


def apply_migration():
    """Alter existing ESBL tables to support beta-lactam spectrum prediction."""
    print("\n🔄 Mode: MIGRATE — Altering existing ESBL tables...\n")
    path = os.path.join(DATABASE_DIR, MIGRATION_SCRIPT)
    if not os.path.exists(path):
        print(f"  ❌ Migration script not found at: {path}")
        sys.exit(1)

    with engine.begin() as conn:
        run_sql_file(path, conn)

    print("\n✅ Migration applied successfully.\n")
    print("   Columns changed:")
    print("   • esbl_encounters: removed esbl_probability, risk_group, threshold_version")
    print("     → added predicted_beta_lactam_spectrum, top_generation_recommendation,")
    print("       predicted_success_probability, spectrum_ood_warning, top_feature_influences")
    print("   • esbl_lab_results: added generation column (backfilled from antibiotic name)")
    print("   • esbl_audit_logs:  removed esbl_probability, top_recommendation,")
    print("     recommendation_efficacy, stewardship_domain")
    print("     → added predicted_beta_lactam_spectrum, top_generation_recommendation,")
    print("       traffic_light_summary, predicted_success_probability,")
    print("       top_feature_influences, clinician_override, override_reason\n")


def verify_tables(conn):
    """Quick check to confirm the tables exist after setup."""
    tables_to_check = [
        "beta_lactam_encounters",
        "beta_lactam_lab_results",
        "beta_lactam_audit_logs",
        "antibiotic_generation_map",
    ]
    missing = []
    for table in tables_to_check:
        result = conn.execute(text(
            f"SELECT to_regclass('public.{table}')"
        )).scalar()
        if result is None:
            missing.append(table)

    if missing:
        print(f"  ⚠️  Tables not found (may be using migrated names): {missing}")
    else:
        print("  ✅ All beta-lactam tables verified in database.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Apply beta-lactam spectrum prediction database schema."
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Create new tables from scratch (use for new environments)."
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Alter existing ESBL tables in-place (use for live environments with data)."
    )
    args = parser.parse_args()

    if args.fresh:
        apply_fresh()
    elif args.migrate:
        apply_migration()
    else:
        print("❌ Please specify --fresh or --migrate.")
        print("   --fresh   : Creates new tables from scratch")
        print("   --migrate : Alters existing ESBL tables (in-place, keeps data)")
        sys.exit(1)

    # Verify (only matters for --fresh mode)
    if args.fresh:
        print("\n🔍 Verifying table creation...\n")
        with engine.connect() as conn:
            verify_tables(conn)

    print("\n🎯 Step 1 (Database Schema) complete.\n")
    print("   Next: Run apply_beta_lactam_service.py (Step 2 — Backend Service)\n")
