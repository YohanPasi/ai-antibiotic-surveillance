
"""
STP Stage 4: SHAP Stability (M54)
---------------------------------
Quantifies consistency of model explanations over time.
ENFORCES M54: Jaccard Similarity of Top-K Features.
"""

import numpy as np
from typing import List, Set, Any

def compute_jaccard_similarity(list_a: List[str], list_b: List[str]) -> float:
    """
    Jaccard Index = intersection / union.
    """
    set_a = set(list_a)
    set_b = set(list_b)
    
    if len(set_a) == 0 and len(set_b) == 0:
        return 1.0 # Both empty -> identical stability (vacuum)
        
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    
    return intersection / union

def assess_explanation_stability(
    current_top_features: List[str],
    previous_top_features: List[str]
) -> dict:
    """
    Computes stability metric (M54) for reporting.
    """
    j_score = compute_jaccard_similarity(current_top_features, previous_top_features)
    
    return {
        "jaccard_index": float(j_score),
        "stable_features": list(set(current_top_features).intersection(set(previous_top_features))),
        "new_features": list(set(current_top_features) - set(previous_top_features)),
        "dropped_features": list(set(previous_top_features) - set(current_top_features))
    }
