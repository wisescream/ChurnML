"""Unit tests for preprocessing utilities."""

from __future__ import annotations

import pandas as pd

from src.data.preprocessing import preprocess_dataframe


def _sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customerID": ["0001", "0002"],
            "gender": ["Female", "Male"],
            "SeniorCitizen": [0, 1],
            "Partner": ["Yes", "No"],
            "Dependents": ["No", "Yes"],
            "tenure": [5, 24],
            "PhoneService": ["Yes", "Yes"],
            "MultipleLines": ["No", "Yes"],
            "InternetService": ["DSL", "Fiber optic"],
            "OnlineSecurity": ["No", "Yes"],
            "OnlineBackup": ["Yes", "No"],
            "DeviceProtection": ["No", "Yes"],
            "TechSupport": ["No", "No"],
            "StreamingTV": ["Yes", "No"],
            "StreamingMovies": ["Yes", "No"],
            "Contract": ["Month-to-month", "Two year"],
            "PaperlessBilling": ["Yes", "No"],
            "PaymentMethod": ["Electronic check", "Credit card (automatic)"],
            "MonthlyCharges": [70.35, 89.10],
            "TotalCharges": [345.78, 2138.56],
            "Churn": ["No", "Yes"],
        }
    )


def test_preprocess_dataframe_outputs_features_and_target() -> None:
    df = _sample_dataframe()
    features, target, pipeline = preprocess_dataframe(df)

    assert features.shape[0] == len(df)
    assert target.tolist() == [0, 1]
    # Ensure pipeline can transform new data without fitting again
    transformed = pipeline.transform(df.drop(columns=["Churn"]))
    assert transformed.shape[0] == len(df)


def test_preprocess_handles_churn_label_and_value_columns() -> None:
    df = _sample_dataframe().rename(columns={"Churn": "Churn Label"})
    df["Churn Value"] = [0, 1]

    features, target, pipeline = preprocess_dataframe(df)

    assert features.shape[0] == len(df)
    assert target.tolist() == [0, 1]

    included_columns: list[str] = []
    for _, _, cols in pipeline.transformers_:
        included_columns.extend(cols)

    assert "Churn Value" not in included_columns