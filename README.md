# Telecom Customer Churn Prediction – MLOps Pipeline

This repository contains a production-oriented MLOps implementation for predicting telecom customer churn. It spans end-to-end workflows from data ingestion and preprocessing, through experiment tracking and model versioning, to API deployment, CI/CD, and monitoring.

## 🔧 Tech Stack

- **Data orchestration:** Apache Airflow
- **Experiment tracking & model registry:** MLflow
- **Versioning:** Git + DVC
- **Modeling:** scikit-learn / XGBoost
- **Serving:** FastAPI + Uvicorn
- **Infrastructure:** Docker, AWS ECR + ECS Fargate
- **Monitoring:** Prometheus + Grafana

## 📁 Project Structure

```
.
├── airflow/                 # Airflow DAGs, Dockerfile, requirements
├── ci-cd/                   # GitHub Actions workflow
├── data/                    # Raw and processed datasets (DVC tracked)
├── deployment/              # FastAPI app and Dockerfile
├── monitoring/              # Prometheus + Grafana configs
├── notebooks/               # Exploratory analysis
├── scripts/                 # Automation helpers (DVC remote, ECS deployment)
├── src/                     # Reusable Python modules (data, models, utils)
├── docker-compose.yml       # Local orchestration (Airflow + API)
├── dvc.yaml                 # Data & model pipeline definition
├── params.yaml              # Hyperparameters and training config
├── requirements.txt         # Shared Python dependencies
└── setup.py                 # Packaging metadata
```

## 🚀 Getting Started

1. **Install dependencies** (Python 3.11+):

	```powershell
	python -m venv .venv
	.\.venv\Scripts\Activate
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	```

2. **Configure DVC and MLflow**:
	- Use the helper script to register a default remote (reads `DVC_REMOTE_URL` if `--url` omitted):

	  ```powershell
	  python scripts/setup_dvc_remote.py --url s3://<your-s3-bucket>/dvc
	  dvc push
	  ```

	  Optional environment variables: `DVC_REMOTE_ENDPOINT`, `DVC_REMOTE_PROFILE`, `DVC_REMOTE_CREDENTIALPATH`.

	Before running, export credentials compatible with your backend (for AWS S3-based remotes, set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optionally `AWS_SESSION_TOKEN`).

	- Set MLflow tracking URI via environment variable or `mlflow ui --backend-store-uri mlruns`.

3. **Reproduce the training pipeline**:

	```powershell
	dvc repro
	```

	Outputs are saved in `data/processed/`, `models/`, and tracked by DVC & MLflow.

## 🧮 Data & Modeling Workflow

- `src/data/preprocessing.py` builds a reusable scikit-learn pipeline (imputation, scaling, encoding) and persists it for inference.
- `src/models/train_model.py` orchestrates preprocessing, trains a RandomForest/XGBoost classifier based on `params.yaml`, logs metrics & artifacts to MLflow, and writes metrics for DVC.
- `src/models/predict_model.py` loads the persisted artifacts and exposes high-level prediction helpers.
- Parameters (algorithms, hyperparameters, validation split) are configurable through `params.yaml`.
- Derived artifacts (`data/processed/`, `models/`, `metrics.json`) are reproduced via `dvc repro` and ignored by Git—see `data/README.md` for the storage policy.

Run the trainer manually:

```powershell
python -m src.models.train_model --project-root .
```

## 📡 Airflow Data Pipeline

The DAG (`airflow/dags/data_pipeline.py`) performs:

1. Raw dataset validation/loading.
2. Preprocessing with the shared pipeline.
3. Persisting processed data to `data/processed/churn_processed.csv`.
4. Optional training trigger (guarded by `ENABLE_AUTOMATED_TRAINING`).

Build and run locally:

```powershell
docker build -f airflow/Dockerfile -t churn-airflow .
docker run -p 8080:8080 churn-airflow
```

Refer to the [Airflow documentation](https://airflow.apache.org/docs/) for scheduler/webserver configuration.

## 🌐 FastAPI Inference Service

- `deployment/app/main.py` exposes `/predict` for batch probability inference and `/health` for readiness checks.
- Input validation uses Pydantic models (`deployment/app/schemas.py`).
- Model assets are loaded via the shared predictor utilities and cached for performance.

Build & run locally:

```powershell
docker build -f deployment/Dockerfile -t churn-api .
docker run -p 8080:8080 -e MODEL_OUTPUT_PATH=/app/models/churn_model.pkl churn-api
```

More on FastAPI: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

## 📦 Docker Compose (Local Stack)

`docker-compose.yml` provides a baseline for bootstrapping Airflow + FastAPI + Prometheus/Grafana locally. Update volume mounts and environment variables as needed before running `docker-compose up`.

## 🧪 CI/CD Pipeline

GitHub Actions workflow (`ci-cd/mlops_pipeline.yml`) executes on pushes to `main`:

1. Install dependencies and run lint/tests.
2. Build Docker images for Airflow and the API.
3. Scan container images with Trivy for critical/high vulnerabilities.
4. Push images to AWS ECR.
5. Update the ECS Fargate service for zero-downtime deployment.

Set the following secrets in your repository: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `ECR_REGISTRY`, and optionally `ECS_TASK_DEFINITION` if you extend the deployment step.

### Deployment automation helper

After a successful pipeline run (or locally when testing), you can register a new ECS task definition and roll the service with:

```powershell
python scripts/deploy_to_ecs.py \
	--cluster telecom-churn-cluster \
	--service telecom-churn-api-svc \
	--image ${env:ECR_REGISTRY}/telecom-churn-api:${env:GITHUB_SHA}
```

Provide extra template substitutions via `--set KEY=VALUE` or environment variables referenced in `deployment/ecs/telecom-churn-api-task.json`.

Ensure AWS credentials are available in the execution environment (standard SDK variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, and optionally `AWS_SESSION_TOKEN`) so the script can register task definitions.

## ☁️ AWS Deployment Blueprint

| Resource | Recommended name | Example ARN | Notes |
| --- | --- | --- | --- |
| ECR repository (Airflow) | `telecom-churn-airflow` | `arn:aws:ecr:us-east-1:123456789012:repository/telecom-churn-airflow` | Receives the image built from `airflow/Dockerfile`. |
| ECR repository (API) | `telecom-churn-api` | `arn:aws:ecr:us-east-1:123456789012:repository/telecom-churn-api` | Receives the image built from `deployment/Dockerfile`. |
| S3 bucket | `mlops-churn-data` | `arn:aws:s3:::mlops-churn-data` | Stores raw data, processed outputs, and the DVC remote (`s3://mlops-churn-data/dvc`). |
| ECS cluster | `telecom-churn-cluster` | `arn:aws:ecs:us-east-1:123456789012:cluster/telecom-churn-cluster` | Hosts the Fargate services. |
| ECS service (API) | `telecom-churn-api-svc` | `arn:aws:ecs:us-east-1:123456789012:service/telecom-churn-cluster/telecom-churn-api-svc` | Runs the FastAPI task definition. |
| ECS service (Airflow) | `telecom-churn-airflow-svc` | `arn:aws:ecs:us-east-1:123456789012:service/telecom-churn-cluster/telecom-churn-airflow-svc` | Optional: webserver/scheduler split or single-service pattern. |
| Task execution role | `telecom-churn-task-exec` | `arn:aws:iam::123456789012:role/telecom-churn-task-exec` | Grants pull access to ECR + CloudWatch logs. |
| Task role | `telecom-churn-task` | `arn:aws:iam::123456789012:role/telecom-churn-task` | Grants runtime access to S3, Secrets Manager, etc. |

### Required GitHub Secrets / Variables

- `AWS_REGION=us-east-1`
- `AWS_ACCOUNT_ID=123456789012`
- `ECR_REGISTRY=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com`
- `ECS_CLUSTER=telecom-churn-cluster`
- `ECS_API_SERVICE=telecom-churn-api-svc`
- `ECS_API_TASK_DEF=telecom-churn-api`
- `ECS_AIRFLOW_SERVICE=telecom-churn-airflow-svc`
- `ECS_AIRFLOW_TASK_DEF=telecom-churn-airflow`

Populate IAM credentials via `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` with least-privileged users that can push to ECR and update the ECS services.

### ECS Task Definition Tips

1. Reference the freshly pushed image:

	 ```json
	 {
		 "image": "${ECR_REGISTRY}/telecom-churn-api:${GITHUB_SHA}",
		 "essential": true,
		 "environment": [
			 {"name": "MODEL_OUTPUT_PATH", "value": "/models/churn_model.pkl"},
			 {"name": "MLFLOW_TRACKING_URI", "value": "s3://mlops-churn-data/mlflow"},
			 {"name": "AWS_REGION", "value": "${AWS_REGION}"}
		 ]
	 }
	 ```

2. Attach the task role (`telecom-churn-task`) with inline policies for:
	 - `s3:GetObject`, `s3:PutObject` on the bucket prefixes used by data/DVC/artifacts.
	 - `logs:CreateLogStream` and `logs:PutLogEvents` for your log group (e.g., `/ecs/telecom-churn-api`).
	 - Optional: `secretsmanager:GetSecretValue` if you store database/API credentials.

3. Set desired count > 1 for rolling deployments, or enable ECS circuit breaker + health checks when operating single-instance services.

4. FastAPI container exposes `8080` by default; ensure the target group/listener matches.

## 📈 Monitoring

- Prometheus scrapes FastAPI (`/metrics`) and the Airflow webserver via `monitoring/prometheus.yml`.
- Grafana dashboard (`monitoring/grafana-dashboard.json`) visualizes latency, throughput, and error rates.
- Export FastAPI metrics using [`prometheus-client`](https://github.com/prometheus/client_python) integration (add middleware as needed).

## 📓 Exploratory Analysis

`notebooks/churn_eda.ipynb` contains starter code for visual exploration (pandas, seaborn, matplotlib). Use it to understand churn patterns, feature correlations, and distribution shifts.

## 🔗 Documentation References

- [Apache Airflow](https://airflow.apache.org/docs/)
- [MLflow](https://mlflow.org/docs/latest/index.html)
- [FastAPI](https://fastapi.tiangolo.com/)
- [DVC](https://dvc.org/doc)
- [AWS ECS](https://docs.aws.amazon.com/ecs/)

## ✅ Next Steps

- Enrich the raw dataset and expand the EDA notebook to capture seasonal/customer-segment trends.
- Introduce IaC (e.g., Terraform or AWS CDK) for reproducible provisioning of the blueprint resources.
- Add automated drift monitoring and scheduled retraining triggers via Airflow or SageMaker Pipelines.
- Extend security posture with KMS-encrypted buckets, VPC endpoints, and automated container re-scanning in production.
- Adopt the release checklist in `docs/RELEASE_CHECKLIST.md` before pushing changes to enforce repeatable quality gates.
