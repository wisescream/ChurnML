"""Shared utilities used across the MLOps churn pipeline."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict

import yaml


def get_logger(name: str = "mlops.churn") -> logging.Logger:
	"""Return a configured logger with a consistent format."""

	logger = logging.getLogger(name)
	if not logger.handlers:
		handler = logging.StreamHandler()
		formatter = logging.Formatter(
			"%(asctime)s - %(name)s - %(levelname)s - %(message)s"
		)
		handler.setFormatter(formatter)
		logger.addHandler(handler)
		logger.setLevel(logging.INFO)
	return logger


def load_params(params_path: Path | str = "params.yaml") -> Dict[str, Any]:
	"""Load project parameters from the YAML configuration file."""

	path = Path(params_path)
	if not path.exists():
		raise FileNotFoundError(f"Params file not found at {path.resolve()}")

	with path.open("r", encoding="utf-8") as fp:
		return yaml.safe_load(fp)


def ensure_dir(directory: Path | str) -> Path:
	"""Create the directory if it does not exist and return its Path."""

	path = Path(directory)
	path.mkdir(parents=True, exist_ok=True)
	return path


def get_env_path(env_var: str, default: Path | str) -> Path:
	"""Fetch a path from an environment variable with a sensible default."""

	value = os.getenv(env_var)
	if value:
		return Path(value)
	return Path(default)
