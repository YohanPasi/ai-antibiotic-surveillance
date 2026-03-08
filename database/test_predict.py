"""
Stage 5 verification — tests the full prediction pipeline end-to-end.
Run: docker exec ast_api python /app/database_scripts/test_predict.py
"""
import sys
sys.path.insert(0, '/app')

from mrsa_consensus_service import consensus_service

test_cases = [
    {
        "name": "High-risk ICU blood (expect RED)",
        "input": {
            "ward": "ICU",
            "sample_type": "Blood",
            "gram_stain": "GPC",
            "cell_count_category": "HIGH",
            "growth_time": 18.5,
            "recent_antibiotic_use": "Yes",
            "length_of_stay": 14,
        }
    },
    {
        "name": "Low-risk ward urine (expect GREEN/AMBER)",
        "input": {
            "ward": "General",
            "sample_type": "Urine",
            "gram_stain": "Unknown",
            "cell_count_category": "LOW",
            "growth_time": None,   # non-blood → -1 sentinel applied
            "recent_antibiotic_use": "No",
            "length_of_stay": 2,
        }
    },
    {
        "name": "Old schema field rejection (age should be ignored)",
        "input": {
            "ward": "Ward 3",
            "sample_type": "Pus",
            "gram_stain": "GPC",
            "cell_count_category": "MEDIUM",
            "growth_time": None,
            "recent_antibiotic_use": "Unknown",
            "length_of_stay": 5,
        }
    },
]

print("=" * 60)
print("Stage 5 Prediction Service — Live Test")
print("=" * 60)

all_passed = True
for tc in test_cases:
    print(f"\n▶ {tc['name']}")
    try:
        result = consensus_service.predict_consensus(tc["input"])
        print(f"  Band:        {result['consensus_band']}")
        print(f"  Probability: {result['consensus_probability']}")
        print(f"  Confidence:  {result['confidence_level']}")
        print(f"  RF={result['models']['rf']['prob']} ({result['models']['rf']['band']})")
        print(f"  LR={result['models']['lr']['prob']} ({result['models']['lr']['band']})")
        print(f"  XGB={result['models']['xgb']['prob']} ({result['models']['xgb']['band']})")
        print(f"  ✅ PASS")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        all_passed = False

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED")
print("=" * 60)
