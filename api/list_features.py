import joblib
import os

ARTIFACT_DIR = "/app/models/mrsa_artifacts"
print("Loading preprocessor...")
try:
    preprocessor = joblib.load(os.path.join(ARTIFACT_DIR, 'mrsa_preprocessor.pkl'))
    # The preprocessor is a ColumnTransformer.
    # We want the 'cat' transformer (OneHotEncoder).
    ohe = preprocessor.named_transformers_['cat']
    
    # categories_ is a list of arrays, one for each categorical feature
    # Order: ward, sample_type, pus_type, gram_positivity, gender
    # (Based on train_mrsa_model.py logic)
    
    print("\n--- WARDS ---")
    print(list(ohe.categories_[0]))
    
    print("\n--- SAMPLE TYPES ---")
    print(list(ohe.categories_[1]))

except Exception as e:
    print(f"Error: {e}")
