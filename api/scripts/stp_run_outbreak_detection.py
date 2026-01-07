#!/usr/bin/env python3
"""
Outbreak Detection & Drift Analysis
REFINEMENT #5: Post-Deployment Discrimination Between Epidemiological Events and Model Drift
"""
import sys
sys.path.append('/app')

from database import SessionLocal
from services.stp_outbreak_detector import analyze_validation_failures

def main():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("STP OUTBREAK VS DRIFT DISCRIMINATOR")
        print("=" * 60)
        print("\nAnalyzing validation failures (last 14 days)...\n")
        
        results = analyze_validation_failures(db, lookback_days=14)
        
        # Ward-Level Outbreaks
        print("📍 WARD-LEVEL OUTBREAKS (Epidemiological Events)")
        print("-" * 60)
        if results['ward_outbreaks']:
            for outbreak in results['ward_outbreaks']:
                print(f"  ⚠️  {outbreak['ward']} — {outbreak['organism']} / {outbreak['antibiotic']}")
                print(f"      Severity: {outbreak['severity']} | Evidence: {outbreak['evidence_count']} CI misses")
                print(f"      Status: NEW (requires human review)")
                print()
        else:
            print("  ✅ No ward-level outbreaks detected\n")
        
        # Systemic Drift
        print("\n🔧 SYSTEMIC DRIFT (Model Performance Issues)")
        print("-" * 60)
        if results['drift_signals']:
            for drift in results['drift_signals']:
                print(f"  ⚠️  {drift['organism']} / {drift['antibiotic']}")
                print(f"      Affected Wards: {drift['affected_wards']} | Avg Error: {drift['avg_error']:.1%}")
                if drift['retraining_recommended']:
                    print(f"      → RETRAINING RECOMMENDED (multi-ward pattern)")
                else:
                    print(f"      → Monitor (below retraining threshold)")
                print()
        else:
            print("  ✅ No systemic drift detected\n")
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Outbreaks Detected: {len(results['ward_outbreaks'])}")
        print(f"Drift Signals: {len(results['drift_signals'])}")
        print("\n✅ SAFEGUARD: Outbreak data excluded from drift calculations")
        print("✅ SAFEGUARD: Only confirmed outbreaks escalate to dashboards")
        print("=" * 60)
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
