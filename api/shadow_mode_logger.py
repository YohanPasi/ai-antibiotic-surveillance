"""
shadow_mode_logger.py
======================
Beta-Lactam CDSS — Shadow-Mode Pilot Logging Engine (Step 9).

Purpose:
  For each patient encounter, records:
    - Day-0 empiric prediction (AI spectrum + top generation)
    - Day-3 actual AST results (True microbiological outcome)
  Then computes standard epidemiological metrics per generation:
    NPV, Sensitivity, Specificity, and AUROC.

Usage:
  Called by POST /api/beta-lactam/shadow-outcome when a nurse or lab tech
  confirms the final AST result for a prior empiric prediction.

Output:
  - shadow_outcomes.jsonl  — line-per-encounter audit log
  - Weekly report JSON     — stewardship stats per generation
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger("shadow_mode")

SHADOW_LOG_PATH = os.path.join(os.path.dirname(__file__), "shadow_outcomes.jsonl")

GENERATIONS = ["Gen1", "Gen2", "Gen3", "Gen4", "Carbapenem", "BL_Combo"]


# ── Record a single outcome ──────────────────────────────────────────────────

def record_shadow_outcome(
    encounter_id:       str,
    empiric_generation: str,
    predicted_spectrum: Dict,       # e.g. {"Gen1": {"probability": 0.91, "traffic_light": "Green"}, ...}
    ast_panel:          Dict[str, str],  # e.g. {"Cefazolin": "S", "Meropenem": "S"}
    generation_map:     Dict[str, str],  # e.g. {"Cefazolin": "Gen1", "Meropenem": "Carbapenem"}
    patient_meta:       Optional[Dict] = None
) -> Dict:
    """
    Save a Day-3 outcome alongside the Day-0 AI prediction for retrospective analysis.

    Returns a summary dict with the de-escalation decision and per-gen correctness flags.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Map AST results to generation-level susceptibility
    gen_susceptible: Dict[str, bool] = {}
    for drug, result in ast_panel.items():
        gen = generation_map.get(drug)
        if gen:
            # Susceptible if ANY drug in that generation is Susceptible
            gen_susceptible[gen] = gen_susceptible.get(gen, False) or (result == "S")

    # Per-generation prediction correctness
    per_gen_outcome: Dict[str, Dict] = {}
    for gen in GENERATIONS:
        predicted_green = predicted_spectrum.get(gen, {}).get("traffic_light") == "Green"
        actual_susceptible = gen_susceptible.get(gen, None)

        if actual_susceptible is None:
            verdict = "UNKNOWN"  # No AST data for this generation
        elif predicted_green and actual_susceptible:
            verdict = "TRUE_GREEN"   # Predicted susceptible, was susceptible → Correct
        elif predicted_green and not actual_susceptible:
            verdict = "FALSE_GREEN"  # Predicted susceptible but resistant → Dangerous!
        elif not predicted_green and actual_susceptible:
            verdict = "FALSE_RED"    # Predicted resistant but actually susceptible → Missed de-escalation
        else:
            verdict = "TRUE_RED"     # Predicted resistant, was resistant → Correct

        per_gen_outcome[gen] = {
            "predicted_traffic_light": predicted_spectrum.get(gen, {}).get("traffic_light", "UNKNOWN"),
            "actual_susceptible": actual_susceptible,
            "verdict": verdict
        }

    # Was there a de-escalation opportunity?
    empiric_gen_idx = GENERATIONS.index(empiric_generation) if empiric_generation in GENERATIONS else -1
    de_escalation_possible = any(
        gen_susceptible.get(GENERATIONS[i], False)
        for i in range(min(empiric_gen_idx, len(GENERATIONS)))
    ) if empiric_gen_idx > 0 else False

    log_entry = {
        "encounter_id":       encounter_id,
        "timestamp":          timestamp,
        "empiric_generation": empiric_generation,
        "predicted_spectrum": predicted_spectrum,
        "ast_panel":          ast_panel,
        "gen_susceptible":    gen_susceptible,
        "per_gen_outcome":    per_gen_outcome,
        "de_escalation_possible": de_escalation_possible,
        "patient_meta":       patient_meta or {}
    }

    # Append to JSONL
    with open(SHADOW_LOG_PATH, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    logger.info(f"📊 Shadow outcome recorded: {encounter_id} | De-escalation possible: {de_escalation_possible}")
    return log_entry


# ── Weekly stewardship report ─────────────────────────────────────────────────

def compute_weekly_report() -> Dict:
    """
    Reads all shadow_outcomes.jsonl entries and computes per-generation:
      - True Green (TP), False Green (FP), True Red (TN), False Red (FN)
      - Sensitivity = TP / (TP + FN)
      - Specificity = TN / (TN + FP)
      - NPV         = TN / (TN + FN)
      - Carbapenem-days avoided (number of encounters where de-escalation was possible)
    """
    if not os.path.exists(SHADOW_LOG_PATH):
        return {"error": "No shadow outcomes recorded yet."}

    counters: Dict[str, Dict] = {
        gen: {"TP": 0, "FP": 0, "TN": 0, "FN": 0} for gen in GENERATIONS
    }
    carbapenem_days_avoided = 0
    total_encounters = 0

    with open(SHADOW_LOG_PATH, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            total_encounters += 1
            if entry.get("de_escalation_possible"):
                carbapenem_days_avoided += 1

            for gen, outcome in entry.get("per_gen_outcome", {}).items():
                v = outcome.get("verdict", "UNKNOWN")
                if v == "TRUE_GREEN":  counters[gen]["TP"] += 1
                elif v == "FALSE_GREEN": counters[gen]["FP"] += 1
                elif v == "TRUE_RED":  counters[gen]["TN"] += 1
                elif v == "FALSE_RED": counters[gen]["FN"] += 1

    report = {
        "generated_at":          datetime.now(timezone.utc).isoformat(),
        "total_encounters":      total_encounters,
        "carbapenem_days_avoided": carbapenem_days_avoided,
        "per_generation_metrics": {}
    }

    for gen, c in counters.items():
        tp, fp, tn, fn = c["TP"], c["FP"], c["TN"], c["FN"]
        sensitivity = round(tp / (tp + fn), 4) if (tp + fn) > 0 else None
        specificity = round(tn / (tn + fp), 4) if (tn + fp) > 0 else None
        npv         = round(tn / (tn + fn), 4) if (tn + fn) > 0 else None
        ppv         = round(tp / (tp + fp), 4) if (tp + fp) > 0 else None

        report["per_generation_metrics"][gen] = {
            "true_green":  tp,
            "false_green": fp,
            "true_red":    tn,
            "false_red":   fn,
            "sensitivity": sensitivity,
            "specificity": specificity,
            "NPV":         npv,
            "PPV":         ppv,
        }

    return report
