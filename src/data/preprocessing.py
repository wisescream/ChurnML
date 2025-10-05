"""Reusable preprocessing components for the telecom churn project."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Tuple

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.utils.helpers import ensure_dir, get_logger

LOGGER = get_logger(__name__)


_TARGET_CANDIDATES = [
	"Churn",
	"Churn Label",
	"churn",
	"churn_label",
	"Churn_Label",
	"Churn Value",
]


def _resolve_target_column(df: pd.DataFrame, preferred: Optional[str]) -> str:
	"""Return the name of the churn column, supporting common dataset variants."""

	search_order = []
	if preferred:
		search_order.append(preferred)
	search_order.extend(_TARGET_CANDIDATES)

	for candidate in search_order:
		if candidate in df.columns:
			LOGGER.debug("Resolved target column to '%s'", candidate)
			return candidate

	available = ", ".join(df.columns[:20])
	raise KeyError(
		"No churn target column found. Checked candidates %s. Available columns: %s"
		% (_TARGET_CANDIDATES, available)
	)


def _detect_feature_types(
	df: pd.DataFrame, target_column: str
) -> Tuple[list[str], list[str]]:
	"""Infer numerical and categorical features from the dataframe."""

	categorical = []
	numerical = []
	for column in df.columns:
		if column == target_column:
			continue
		if pd.api.types.is_numeric_dtype(df[column]):
			numerical.append(column)
		else:
			categorical.append(column)
	return numerical, categorical


def build_preprocessing_pipeline(
	df: pd.DataFrame,
	target_column: str = "Churn",
	numerical_features: Optional[Iterable[str]] = None,
	categorical_features: Optional[Iterable[str]] = None,
) -> ColumnTransformer:
	"""Create a preprocessing pipeline tailored to the dataframe."""

	target_column = _resolve_target_column(df, target_column)

	if numerical_features is None or categorical_features is None:
		inferred_num, inferred_cat = _detect_feature_types(df, target_column)
		numerical_features = list(numerical_features or inferred_num)
		categorical_features = list(categorical_features or inferred_cat)

	LOGGER.info(
		"Building preprocessing pipeline with %d numerical and %d categorical features",
		len(numerical_features),
		len(categorical_features),
	)

	numeric_pipeline = Pipeline(
		steps=[
			("imputer", SimpleImputer(strategy="median")),
			("scaler", StandardScaler()),
		]
	)

	encoder_kwargs: dict[str, object] = {"handle_unknown": "ignore"}
	if "sparse_output" in OneHotEncoder.__init__.__code__.co_varnames:
		encoder_kwargs["sparse_output"] = False
	else:  # pragma: no cover - fallback for older scikit-learn
		encoder_kwargs["sparse"] = False

	categorical_pipeline = Pipeline(
		steps=[
			("imputer", SimpleImputer(strategy="most_frequent")),
			("encoder", OneHotEncoder(**encoder_kwargs)),
		]
	)

	transformer = ColumnTransformer(
		transformers=[
			("num", numeric_pipeline, list(numerical_features)),
			("cat", categorical_pipeline, list(categorical_features)),
		]
	)

	return transformer


def preprocess_dataframe(
	df: pd.DataFrame,
	target_column: str = "Churn",
	pipeline: Optional[ColumnTransformer] = None,
) -> Tuple[pd.DataFrame, pd.Series, ColumnTransformer]:
	"""Fit (when needed) and apply the preprocessing pipeline."""

	target_column = _resolve_target_column(df, target_column)
	duplicate_targets = {
		candidate
		for candidate in _TARGET_CANDIDATES
		if candidate in df.columns and candidate != target_column
	}
	if duplicate_targets:
		LOGGER.info(
			"Dropping potential leakage columns: target='%s', duplicates=%s",
			target_column,
			sorted(duplicate_targets),
		)
	df_model = df.drop(columns=list(duplicate_targets))
	y = df_model[target_column].copy()
	X = df_model.drop(columns=[target_column])

	if pipeline is None:
		pipeline = build_preprocessing_pipeline(df_model, target_column)
		LOGGER.info("Fitting preprocessing pipeline from scratch")
		features = pipeline.fit_transform(X)
	else:
		LOGGER.info("Applying existing preprocessing pipeline")
		features = pipeline.transform(X)

	processed_df = pd.DataFrame(features)
	LOGGER.info("Generated processed feature matrix with shape %s", processed_df.shape)

	# Standardize target values to binary 0/1
	if y.dtype == "O":
		y = y.str.strip().str.lower().map({"yes": 1, "no": 0}).fillna(0).astype(int)

	return processed_df, y, pipeline


def save_pipeline(pipeline: ColumnTransformer, output_path: Path | str) -> None:
	"""Persist the fitted preprocessing pipeline for reuse."""

	path = ensure_dir(Path(output_path).parent) / Path(output_path).name
	joblib.dump(pipeline, path)
	LOGGER.info("Saved preprocessing pipeline to %s", path)


def load_pipeline(pipeline_path: Path | str) -> ColumnTransformer:
	"""Load a previously saved preprocessing pipeline."""

	path = Path(pipeline_path)
	if not path.exists():
		raise FileNotFoundError(f"Preprocessing pipeline not found at {path}")
	LOGGER.info("Loading preprocessing pipeline from %s", path)
	return joblib.load(path)


def save_processed_dataset(
	features: pd.DataFrame,
	target: pd.Series,
	output_path: Path | str,
) -> Path:
	"""Persist processed features and target into a single CSV file."""

	path = Path(output_path)
	ensure_dir(path.parent)
	dataset = features.copy()
	dataset["target"] = target.values
	dataset.to_csv(path, index=False)
	LOGGER.info("Saved processed dataset to %s", path)
	return path
