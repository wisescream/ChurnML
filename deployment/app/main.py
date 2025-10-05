"""FastAPI application exposing churn prediction capabilities."""

from __future__ import annotations

import time
from typing import Awaitable, Callable, List

from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest

from .schemas import (
    PredictionRequest,
    PredictionResponse,
    PredictionResult,
)
from src.models.predict_model import get_predictor
from src.utils.helpers import get_logger

LOGGER = get_logger("fastapi.churn")

app = FastAPI(
	title="Telecom Churn Prediction API",
	description="Predict customer churn probabilities using a trained ML model",
	version="0.1.0",
)


REQUEST_COUNTER = Counter(
	"fastapi_requests_total",
	"Total number of requests processed",
	["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
	"fastapi_request_duration_seconds",
	"Request duration in seconds",
	["method", "path"],
)


@app.on_event("startup")
def _load_model() -> None:
	"""Ensure model artifacts are loaded in memory on startup."""

	try:
		get_predictor()
		LOGGER.info("Churn predictor initialized successfully")
	except FileNotFoundError as exc:
		LOGGER.error("Failed to load predictor: %s", exc)


@app.middleware("http")
async def metrics_middleware(
	request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
	"""Collect Prometheus metrics for each request."""

	start_time = time.perf_counter()
	response = await call_next(request)
	latency = time.perf_counter() - start_time

	path = request.scope.get("path", "unknown")
	method = request.method
	status_code = str(response.status_code)

	REQUEST_COUNTER.labels(method=method, path=path, status=status_code).inc()
	REQUEST_LATENCY.labels(method=method, path=path).observe(latency)

	return response


@app.get("/health", tags=["health"])
def health_check() -> dict:
	"""Return basic health information for the service."""

	return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse, tags=["inference"])
def predict(request: PredictionRequest) -> PredictionResponse:
	"""Predict churn probabilities for the provided customers."""

	if not request.customers:
		raise HTTPException(status_code=400, detail="Request contains no customers")

	predictor = get_predictor()
	payload: List[dict] = [customer.model_dump() for customer in request.customers]

	probabilities = predictor.predict_proba(payload)
	labels = predictor.predict_label(payload)

	results = [
		PredictionResult(
			customerID=customer.customerID,
			churn_probability=float(probability),
			churn_prediction=int(label),
		)
		for customer, probability, label in zip(request.customers, probabilities, labels)
	]

	LOGGER.info("Generated predictions for %d customers", len(results))
	return PredictionResponse(results=results)


@app.get("/metrics", tags=["monitoring"])
def metrics() -> Response:
	"""Expose Prometheus metrics for scraping."""

	return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
