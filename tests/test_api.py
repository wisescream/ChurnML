"""Tests for FastAPI churn prediction service."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from deployment.app.main import app


class DummyPredictor:
    def predict_proba(self, records):
        return [0.7 for _ in records]

    def predict_label(self, records, threshold=0.5):
        return [1 if 0.7 >= threshold else 0 for _ in records]


@pytest.fixture
def client():
    dummy = DummyPredictor()
    with patch("deployment.app.main.get_predictor", return_value=dummy):
        with TestClient(app) as test_client:
            yield test_client


def test_predict_endpoint_success(client):
    payload = {
        "customers": [
            {
                "customerID": "0001",
                "gender": "Female",
                "SeniorCitizen": 0,
                "Partner": "Yes",
                "Dependents": "No",
                "tenure": 5,
                "PhoneService": "Yes",
                "MultipleLines": "No",
                "InternetService": "DSL",
                "OnlineSecurity": "No",
                "OnlineBackup": "Yes",
                "DeviceProtection": "No",
                "TechSupport": "No",
                "StreamingTV": "Yes",
                "StreamingMovies": "No",
                "Contract": "Month-to-month",
                "PaperlessBilling": "Yes",
                "PaymentMethod": "Electronic check",
                "MonthlyCharges": 70.35,
                "TotalCharges": 345.78,
            }
        ]
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data and len(data["results"]) == 1
    assert data["results"][0]["churn_prediction"] == 1


def test_metrics_endpoint_exposes_prometheus(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "fastapi_requests_total" in body
    assert "fastapi_request_duration_seconds" in body
