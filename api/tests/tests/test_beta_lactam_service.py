import pytest
import sys
import os
import numpy as np

# Add API to path to import service (service is at /app in docker, which is 2 dirs up)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from beta_lactam_service import BetaLactamSpectrumService
from fastapi import HTTPException

@pytest.fixture
def bl_service():
    """Returns a loaded instance of the BetaLactamSpectrumService using our mock artifacts."""
    return BetaLactamSpectrumService()

@pytest.fixture
def mock_patient_data():
    return {
        "Age": "65",
        "Gender": "Male",
        "Ward": "ICU",
        "Organism": "E_coli",
        "Sample_Type": "Urine"
    }

def test_service_initialization(bl_service):
    """Ensure the service loads thresholds and feature names correctly."""
    assert bl_service.feature_names is not None
    assert len(bl_service.feature_names) > 0
    assert "thresholds" in bl_service.thresholds
    assert bl_service.thresholds["thresholds"]["green_min"] == 0.70

def test_feature_masking(bl_service, mock_patient_data):
    """
    Test B: Feature Masking.
    Ensure drugs like Ceftriaxone (CTX) are stripped from input vector.
    """
    # Simulate a patient who had prior exposure to Ceftriaxone
    sneaky_data = mock_patient_data.copy()
    sneaky_data["Prior_Exposure_CTX"] = 1.0  # Should be masked
    
    # Manually add to feature list if not present, just to ensure masking logic fires
    if "Prior_Exposure_CTX" not in bl_service.feature_names:
         bl_service.feature_names.append("Prior_Exposure_CTX")
         
    # Generate feature vector
    vector = bl_service._prepare_features(sneaky_data)
    
    # Find index of Prior_Exposure_CTX
    idx = bl_service.feature_names.index("Prior_Exposure_CTX")
    
    # Assert it was zeroed out by the masking config
    assert vector[0, idx] == 0.0, "Feature Masking Failed: CTX exposure was not zeroed out!"

def test_multi_generation_prediction_shape(bl_service, mock_patient_data):
    """
    Test A: Multi-Generation Prediction
    Ensure the spectrum returns all 6 generations with prob & traffic tight.
    """
    # Bypass governance directly to test ML output
    vector = bl_service._prepare_features(mock_patient_data)
    spectrum = bl_service._predict_spectrum(vector)
    
    expected_gens = ["Gen1", "Gen2", "Gen3", "Gen4", "Carbapenem", "BL_Combo"]
    
    for gen in expected_gens:
        assert gen in spectrum
        assert "probability" in spectrum[gen]
        assert "traffic_light" in spectrum[gen]
        assert 0.0 <= spectrum[gen]["probability"] <= 1.0
        assert spectrum[gen]["traffic_light"] in ["Green", "Amber", "Red"]


def test_bayesian_stewardship_ranking(bl_service):
    """
    Test C: Bayesian Stewardship Ranking
    Ensure narrow spectrums (Gen1) outrank Carbapenems when both are Green.
    """
    # Mock a spectrum where EVERYTHING is highly susceptible
    mock_spectrum = {
        "Gen1": {"probability": 0.95, "traffic_light": "Green"},
        "Carbapenem": {"probability": 0.99, "traffic_light": "Green"}
    }
    
    # Generate rankings for a Low risk patient
    recs = bl_service._generate_recommendations(mock_spectrum, "Low")
    
    # Gen1 should be promoted due to Bayesian evidence table (success/total ratio) and stewardship penalty on Carb
    top_gen = recs[0]["generation"]
    
    # We expect Gen1 to be favored over Carbapenem for a Low risk patient despite Carb having 0.99
    ranked_gens = [r["generation"] for r in recs]
    assert ranked_gens.index("Gen1") < ranked_gens.index("Carbapenem"), "Stewardship Failed: Carbapenem ranked above Gen1 for fully susceptible bug."
    

def test_governance_rules_scope_validation(bl_service):
    """
    Test D: Governance Rules - Scope validation
    """
    # Include all required LIS fields so validate_day0_inputs passes,
    # then validate_scope kicks in and rejects Pseudomonas
    out_of_scope_data = {
        "Organism": "Pseudomonas_aeruginosa",
        "Gram": "GNB",
        "Age": "45",
        "Gender": "Female",
        "Ward": "ICU",
        "Sample_Type": "Blood"
    }
    
    with pytest.raises(HTTPException) as exc_info:
        bl_service.predict_and_evaluate({"inputs": out_of_scope_data, "ast_available": False})
        
    assert exc_info.value.status_code == 400
    assert "not in governance scope" in exc_info.value.detail.lower()

def test_governance_rules_ast_lock(bl_service, mock_patient_data):
    """
    Test D: Governance Rules - AST Lock
    """
    with pytest.raises(HTTPException) as exc_info:
        # Pass ast_available=True to simulate laboratory finalization
        bl_service.predict_and_evaluate({"inputs": mock_patient_data, "ast_available": True})
        
    assert exc_info.value.status_code == 403
    assert "ast results available" in exc_info.value.detail.lower()

def test_ood_detection(bl_service, mock_patient_data):
    """
    Test D: Governance Rules - OOD flags
    """
    # Impossible age to trigger Out-Of-Distribution
    ood_data = mock_patient_data.copy()
    ood_data["Age"] = 150 
    
    is_ood = bl_service.check_ood(ood_data)
    
    assert is_ood is True, "OOD Detection failed: Age 150 was not flagged as outlier."
