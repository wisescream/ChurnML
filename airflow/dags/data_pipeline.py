"""Airflow DAG orchestrating the telecom churn data pipeline."""

from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from airflow import DAG  # type: ignore
from airflow.operators.python import PythonOperator  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.append(str(PROJECT_ROOT))

from src.data.preprocessing import preprocess_dataframe, save_pipeline  # noqa: E402
from src.utils.helpers import ensure_dir, get_logger  # noqa: E402

LOGGER = get_logger("airflow.churn")


DEFAULT_ARGS = {
	"owner": "mlops-team",
	"depends_on_past": False,
	"email_on_failure": False,
	"email_on_retry": False,
	"retries": 1,
	"retry_delay": timedelta(minutes=5),
}


def extract_raw_dataset(**context):
	"""Validate and expose the raw dataset path via XCom."""

	raw_path = Path(os.getenv("RAW_DATA_PATH", PROJECT_ROOT / "data/raw/telecom_churn.csv"))
	if not raw_path.exists():
		raise FileNotFoundError(f"Raw dataset missing at {raw_path}")

	LOGGER.info("Found raw dataset at %s", raw_path)
	context["ti"].xcom_push(key="raw_dataset_path", value=str(raw_path))


def preprocess_dataset(**context):
	"""Clean and preprocess the raw dataset; persist interim artifacts."""

	ti = context["ti"]
	raw_path = Path(ti.xcom_pull(key="raw_dataset_path"))
	df = pd.read_csv(raw_path)

	processed_features, target, pipeline = preprocess_dataframe(df)

	tmp_dir = ensure_dir(Path(os.getenv("AIRFLOW_TMP_DIR", PROJECT_ROOT / "tmp")))
	temp_dataset_path = tmp_dir / "churn_processed_tmp.csv"
	dataset = processed_features.copy()
	dataset["target"] = target
	dataset.to_csv(temp_dataset_path, index=False)
	LOGGER.info("Wrote temporary processed dataset to %s", temp_dataset_path)

	pipeline_path = Path(os.getenv("PIPELINE_PATH", PROJECT_ROOT / "models/preprocessing_pipeline.pkl"))
	save_pipeline(pipeline, pipeline_path)

	ti.xcom_push(key="temp_dataset_path", value=str(temp_dataset_path))
	ti.xcom_push(key="pipeline_path", value=str(pipeline_path))


def persist_processed_dataset(**context):
	"""Move processed dataset into the canonical processed data directory."""

	ti = context["ti"]
	temp_dataset_path = Path(ti.xcom_pull(key="temp_dataset_path"))
	processed_path = Path(
		os.getenv("PROCESSED_DATA_PATH", PROJECT_ROOT / "data/processed/churn_processed.csv")
	)
	ensure_dir(processed_path.parent)
	shutil.move(str(temp_dataset_path), processed_path)
	LOGGER.info("Saved processed dataset to %s", processed_path)
	ti.xcom_push(key="processed_dataset_path", value=str(processed_path))


def trigger_training(**context):
	"""Optionally kick off model training after preprocessing."""

	if os.getenv("ENABLE_AUTOMATED_TRAINING", "false").lower() != "true":
		LOGGER.info("Automated training disabled via ENABLE_AUTOMATED_TRAINING env var")
		return

	processed_path = context["ti"].xcom_pull(key="processed_dataset_path")
	pipeline_path = context["ti"].xcom_pull(key="pipeline_path")

	LOGGER.info(
		"Training step triggered with dataset=%s and pipeline=%s", processed_path, pipeline_path
	)
	# Placeholder for an Airflow TriggerDagRunOperator or KubernetesPodOperator call.
	# Real implementation would submit a training job or call an API endpoint.


with DAG(
	dag_id="telecom_churn_data_pipeline",
	description="Extract, preprocess, and persist telecom churn data",
	schedule_interval=os.getenv("DATA_PIPELINE_SCHEDULE", "0 2 * * *"),
	default_args=DEFAULT_ARGS,
	catchup=False,
	start_date=datetime(2024, 1, 1),
	tags=["mlops", "churn"],
) as dag:
	extract_task = PythonOperator(
		task_id="extract_raw_dataset",
		python_callable=extract_raw_dataset,
		provide_context=True,
	)

	preprocess_task = PythonOperator(
		task_id="preprocess_dataset",
		python_callable=preprocess_dataset,
		provide_context=True,
	)

	persist_task = PythonOperator(
		task_id="persist_processed_dataset",
		python_callable=persist_processed_dataset,
		provide_context=True,
	)

	training_task = PythonOperator(
		task_id="trigger_model_training",
		python_callable=trigger_training,
		provide_context=True,
	)

	extract_task >> preprocess_task >> persist_task >> training_task
