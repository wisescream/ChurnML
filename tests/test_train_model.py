"""Regression tests for the training CLI entrypoint."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pandas as pd

from src.models import train_model


def test_train_cli_produces_expected_artifacts(tmp_path, monkeypatch):
	"""Running the CLI should materialize model, pipeline, metrics, and processed data."""

	project_root = tmp_path
	data_dir = project_root / "data" / "raw"
	data_dir.mkdir(parents=True, exist_ok=True)

	df = pd.DataFrame(
		{
			"customerID": [f"000{i}" for i in range(10)],
			"tenure": [1, 3, 5, 2, 4, 6, 8, 7, 9, 10],
			"MonthlyCharges": [29.99, 49.99, 59.99, 39.99, 54.99, 64.99, 69.99, 74.99, 79.99, 89.99],
			"Contract": [
				"Month-to-month",
				"One year",
				"Two year",
				"Month-to-month",
				"Month-to-month",
				"One year",
				"Two year",
				"Month-to-month",
				"One year",
				"Two year",
			],
			"Churn": ["No", "Yes", "No", "No", "Yes", "No", "Yes", "No", "No", "Yes"],
		}
	)
	df.to_csv(data_dir / "telecom_churn.csv", index=False)

	params = {
		"train": {
			"experiment_name": "test-experiment",
			"validation_split": 0.3,
			"random_state": 42,
			"model_type": "random_forest",
			"random_forest": {
				"n_estimators": 10,
				"max_depth": 4,
			},
		},
	}
	params_path = project_root / "params.yaml"
	params_path.write_text(json.dumps(params), encoding="utf-8")

	def _fake_parse_args() -> SimpleNamespace:  # type: ignore[override]
		return SimpleNamespace(project_root=project_root, params=params_path)

	monkeypatch.setattr(train_model, "parse_args", _fake_parse_args)

	train_model.main()

	processed_path = project_root / "data" / "processed" / "churn_processed.csv"
	model_path = project_root / "models" / "churn_model.pkl"
	pipeline_path = project_root / "models" / "preprocessing_pipeline.pkl"
	metrics_path = project_root / "metrics.json"
	mlflow_dir = project_root / "mlruns"

	assert processed_path.exists(), "Processed dataset was not created"
	assert model_path.exists(), "Trained model artifact missing"
	assert pipeline_path.exists(), "Preprocessing pipeline artifact missing"
	assert metrics_path.exists(), "Metrics file missing"
	assert mlflow_dir.exists(), "MLflow directory missing"

	metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
	for key in ("accuracy", "f1_score", "roc_auc"):
		assert key in metrics, f"Metric '{key}' missing from metrics.json"