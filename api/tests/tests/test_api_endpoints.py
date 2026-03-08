import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add API to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from main import app
from unittest.mock import patch

class MockDB:
    def execute(self, *args, **kwargs):
        pass
    def commit(self):
        pass
    def close(self):
        pass

# We patch SessionLocal because the real code uses `db = SessionLocal()` directly
# inside the route instead of using Depends(get_db).
patcher = patch('main.SessionLocal', return_value=MockDB())
patcher.start()

client = TestClient(app)

@pytest.fixture
def mock_evaluate_payload():
    return {
        "inputs": {
            "Age": "65",
            "Gender": "Male",
            "Ward": "ICU",
            "Organism": "E_coli",
            "Gram": "GNB",
            "Sample_Type": "Urine",
            "Prior_Exposure_CTX": 0.0
        },
        "ast_available": False
    }

@pytest.fixture
def mock_override_payload():
    return {
        "encounter_id": "TEST_ENC_001",
        "user_id": "Dr. Smith",
        "model_version": "v1.0-test",
        "generation_recommended": "Gen1",
        "decision": "OVERRIDE",
        "reason_code": "CLINICAL_DETERIORATION",
        "selected_generation": "Carbapenem"
    }

@pytest.fixture
def mock_post_ast_payload():
    return {
        "empiric_generation": "Carbapenem",
        "ast_panel": {
            "Ceftriaxone": "S",
            "Cefazolin": "S",
            "Meropenem": "S"
        }
    }

@pytest.fixture
def mock_lab_results_payload():
    return {
        "encounter_id": "TEST_ENC_001",
        "lab_no": "LAB-2023-XYZ",
        "ward": "ICU",
        "specimen_type": "Blood",
        "organism": "E_coli",
        "results": [
            {
                "antibiotic": "Meropenem",
                "result": "S",
                "mic_value": 0.25,
                "breakpoint_standard": "EUCAST"
            },
            {
                "antibiotic": "Ceftriaxone",
                "result": "R",
                "mic_value": 8.0,
                "breakpoint_standard": "EUCAST"
            }
        ]
    }


def test_api_evaluate_endpoint(mock_evaluate_payload):
    """
    Test E: Evaluate Endpoint.
    Ensures POST /api/beta-lactam/evaluate returns a valid spectrum schema.
    """
    response = client.post("/api/beta-lactam/evaluate", json=mock_evaluate_payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "spectrum" in data
    assert "risk_group" in data
    assert "top_generation_recommendation" in data
    assert "recommendations" in data
    
    recs = data["recommendations"]
    assert len(recs) > 0
    assert "generation" in recs[0]
    assert "traffic_light" in recs[0]

def test_api_evaluate_out_of_scope():
    """
    Test E: Scope Rejection at API layer.
    """
    bad_payload = {
        "inputs": {
            "Organism": "Pseudomonas_aeruginosa",
            "Gram": "GNB",
            "Age": "45",
            "Gender": "Female",
            "Ward": "ICU",
            "Sample_Type": "Blood"
        },
        "ast_available": False
    }
    response = client.post("/api/beta-lactam/evaluate", json=bad_payload)
    
    assert response.status_code == 400
    assert "not in governance scope" in response.json()["detail"].lower()

def test_api_override_endpoint(mock_override_payload):
    """
    Test F: Override Governance Endpoint.
    Ensures POST /api/beta-lactam/override returns 200 OK.
    (Note: Full DB mock assertion requires dependency injection, but we test the route here).
    """
    response = client.post("/api/beta-lactam/override", json=mock_override_payload)
    
    assert response.status_code == 200
    assert response.json() == {
        "status": "logged",
        "message": "Clinician decision recorded in audit trail."
    }


def test_api_post_ast_review_de_escalation(mock_post_ast_payload):
    """
    Test G: Post-AST Review Endpoint.
    If Empiric was Carbapenem, and AST shows Gen1 (Cefazolin) is Susceptible,
    it MUST recommend de-escalation.
    """
    response = client.post("/api/beta-lactam/post-ast-review", json=mock_post_ast_payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["action"] == "DE_ESCALATION_RECOMMENDED"
    # The actual response has no 'recommended_generation' key — check message field instead
    assert "Gen1" in data["message"]

def test_api_post_lab_results(mock_lab_results_payload):
    """
    Test H: Save Lab Results Endpoint.
    Ensures POST /api/beta-lactam/lab-results returns 200 OK after mock evaluation.
    (Note: Full DB mock assertion requires dependency injection, but we test the route here).
    """
    # Just patch the DB execute inside the route context so it doesn't fail the fetchone() or insert
    with patch('main.SessionLocal') as mock_session_local:
        # Mock the encounter look-up to succeed
        mock_db = mock_session_local.return_value
        mock_db.execute.return_value.fetchone.return_value = {"status": "PENDING"}
        
        response = client.post("/api/beta-lactam/lab-results", json=mock_lab_results_payload)
        
        assert response.status_code == 200
        assert "AST results saved successfully" in response.json()["message"]
