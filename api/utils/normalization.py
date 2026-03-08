"""
Canonical normalization utilities for antibiotic surveillance data.

Two separate functions with different rules:
  - normalize_antibiotic(): strips brackets, underscores, extra spaces
  - normalize_organism():   lowercase + whitespace only (NO bracket stripping)

Used for comparison only — never for display.
Display always uses the canonical DB name + short_code (e.g. "Meropenem (MEM)").
"""

import re


def normalize_antibiotic(name: str) -> str:
    """
    Normalize an antibiotic name for comparison purposes only.

    Handles messy raw dataset names like:
      "Meropenem  (MEM)"         → "meropenem"
      "Piperacillin_Tazobactam"  → "piperacillin-tazobactam"
      "Amikacin  ( AK )"         → "amikacin"
      "Piperacillin-Tazobactam"  → "piperacillin-tazobactam"
    """
    name = name.lower()
    name = name.replace('_', ' ')
    name = name.replace('–', '-').replace('—', '-')   # normalize dashes
    name = re.sub(r'\s*\(.*?\)', '', name)             # strip (MEM), ( AK ), (TZP/PTZ)
    name = re.sub(r'\s+', ' ', name).strip()           # collapse whitespace
    return name


def normalize_organism(name: str) -> str:
    """
    Normalize an organism name for comparison purposes only.

    Rules: lowercase + collapse whitespace ONLY.
    Do NOT strip brackets — organism names don't have bracket codes,
    and stripping would break names like "Acinetobacter spp."

    "Pseudomonas aeruginosa"  → "pseudomonas aeruginosa"
    "  Escherichia coli  "    → "escherichia coli"
    """
    name = name.lower()
    name = re.sub(r'\s+', ' ', name).strip()
    return name
