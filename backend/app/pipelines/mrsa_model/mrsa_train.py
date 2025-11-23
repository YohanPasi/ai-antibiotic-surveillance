import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from lightgbm import LGBMClassifier


# ===========================
# PATH SETUP
# ===========================
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed" / "mrsa"
MODEL_DIR = PROJECT_ROOT / "ml" / "mrsa"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

FILE_L1 = DATA_PROCESSED / "mrsa_light1_clean.parquet"
FILE_L4 = DATA_PROCESSED / "mrsa_light4_clean.parquet"


# ===========================
# FEATURE ENGINEERING HELPERS
# ===========================
def add_time_features(df):
    df["collection_time"] = pd.to_datetime(df["collection_time"], errors="coerce")
    df["hour_of_day"] = df["collection_time"].dt.hour
    df["day_of_week"] = df["collection_time"].dt.weekday
    df["month"] = df["collection_time"].dt.month
    df = df.drop(columns=["collection_time"])
    return df


def encode_categoricals(df, exclude_cols=[]):
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == "object" and col not in exclude_cols:
            df[col] = df[col].astype("category")
    return df



# ===========================
# TRAINING FUNCTION
# ===========================
def train_model(df, feature_type: str):
    print(f"\n=== TRAINING MRSA MODEL ({feature_type}) ===")

    # Ensure correct label
    if "mrsa_label" not in df.columns:
        raise ValueError("mrsa_label not found in dataframe.")

    # Feature engineering
    df = add_time_features(df)
    df = encode_categoricals(df)

    # Separate X / y
    y = df["mrsa_label"].astype(int)
    X = df.drop(columns=["mrsa_label", "sample_id"])

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train LightGBM
    model = LGBMClassifier(
        objective="binary",
        n_estimators=300,
        learning_rate=0.05,
        max_depth=-1,
        subsample=0.9,
        colsample_bytree=0.9,
        class_weight="balanced",
    )

    model.fit(X_train, y_train)

    # Predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    # Metrics
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)

    print("Accuracy:", acc)
    print("ROC-AUC:", auc)
    print("Confusion Matrix:\n", cm)
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    # Save model
    model_path = MODEL_DIR / f"mrsa_{feature_type}.pkl"
    joblib.dump(model, model_path)

    # Save metadata
    summary = {
        "model": f"MRSA {feature_type}",
        "accuracy": float(acc),
        "roc_auc": float(auc),
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "features": list(X.columns),
    }

    summary_path = MODEL_DIR / f"mrsa_{feature_type}_metrics.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=4)

    print(f"Saved model → {model_path}")
    print(f"Saved metrics → {summary_path}")


# ===========================
# MAIN
# ===========================
def main():
    print("=== MRSA MODEL TRAINING STARTED ===")

    df_l1 = pd.read_parquet(FILE_L1)
    df_l4 = pd.read_parquet(FILE_L4)

    # TRAIN MODELS
    train_model(df_l1, "light1")
    train_model(df_l4, "light4")

    print("\n=== MRSA MODEL TRAINING COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
