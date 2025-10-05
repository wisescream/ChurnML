"""Pydantic schemas for the churn prediction FastAPI service."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class CustomerFeatures(BaseModel):
	customerID: str = Field(..., description="Unique customer identifier")
	gender: str
	SeniorCitizen: int = Field(..., ge=0, le=1)
	Partner: str
	Dependents: str
	tenure: int = Field(..., ge=0)
	PhoneService: str
	MultipleLines: str
	InternetService: str
	OnlineSecurity: str
	OnlineBackup: str
	DeviceProtection: str
	TechSupport: str
	StreamingTV: str
	StreamingMovies: str
	Contract: str
	PaperlessBilling: str
	PaymentMethod: str
	MonthlyCharges: float
	TotalCharges: Optional[float]


class PredictionRequest(BaseModel):
	customers: List[CustomerFeatures]


class PredictionResult(BaseModel):
	customerID: str
	churn_probability: float = Field(..., ge=0.0, le=1.0)
	churn_prediction: int = Field(..., ge=0, le=1)


class PredictionResponse(BaseModel):
	results: List[PredictionResult]
