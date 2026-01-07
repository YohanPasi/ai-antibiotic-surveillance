
"""
STP Stage 3: Model Manager
--------------------------
Handles interaction with M29 Model Registry.
- Saves trained models (serialized).
- Logs metrics.
- Retrieves active models for inference.
"""

import os
import json
import joblib
import uuid
import pandas as pd
from datetime import datetime
from typing import Dict, Any

# Assuming DB access via api.database
# We will just write files/JSONs for the prototype or mock DB insert.
# Real implementation would use SQLAlchemy.

MODELS_DIR = "models_store"

def save_model(
    model_obj: Any,
    model_type: str,
    target: str,
    horizon: int,
    stage2_version: str,
    metrics: Dict[str, float],
    features_hash: str = "N/A"
) -> str:
    """
    Serializes model and returning metadata for DB insertion.
    M29: Versioning and Storage.
    """
    
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        
    model_id = str(uuid.uuid4())
    filename = f"{model_type}_{target}_h{horizon}_{model_id}.pkl"
    filepath = os.path.join(MODELS_DIR, filename)
    
    # Serialize
    joblib.dump(model_obj, filepath)
    
    # Metadata Record
    record = {
        'model_id': model_id,
        'model_type': model_type,
        'target': target,
        'horizon': horizon,
        'stage2_version': stage2_version,
        'features_hash': features_hash,
        'metrics_json': json.dumps(metrics),
        'status': 'active',
        'filepath': filepath,
        'created_at': datetime.now().isoformat()
    }
    
    # In a real app, this returns the dict to be INSERTed into stp_model_registry
    return record

def load_model(filepath: str) -> Any:
    """Loads a serialized model."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")
    return joblib.load(filepath)
