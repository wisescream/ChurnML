FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY deployment/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
	&& pip install --no-cache-dir -r /app/requirements.txt

COPY deployment/app /app/app
COPY src /app/src
COPY models /app/models
COPY params.yaml /app/params.yaml

ENV MODEL_OUTPUT_PATH=/app/models/churn_model.pkl
ENV PIPELINE_PATH=/app/models/preprocessing_pipeline.pkl

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
