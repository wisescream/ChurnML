
# Copilot Instructions: Real-World MLOps Pipeline — Telecom Customer Churn Prediction

## Purpose
These instructions are for an AI agent to automatically generate a **production-ready MLOps project** for predicting telecom customer churn. The agent should create the full repository with **Airflow DAGs, ML training scripts, FastAPI deployment, Dockerfiles, CI/CD pipeline, monitoring placeholders, and AWS deployment structure**.

---

## 1️⃣ Project Structure
Create the following folder structure and empty files as placeholders where needed:

```

mlops-churn-prediction/
│
├── .github/
│   └── copilot-instructions.md
│
├── airflow/
│   ├── dags/
│   │   └── data_pipeline.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── data/
│   ├── raw/
│   │   └── telecom_churn.csv
│   └── processed/
│       └── churn_processed.csv
│
├── notebooks/
│   └── churn_eda.ipynb
│
├── src/
│   ├── data/
│   │   └── preprocessing.py
│   ├── models/
│   │   ├── train_model.py
│   │   └── predict_model.py
│   └── utils/
│       └── helpers.py
│
├── deployment/
│   ├── app/
│   │   ├── main.py
│   │   └── schemas.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── ci-cd/
│   └── mlops_pipeline.yml
│
├── monitoring/
│   ├── prometheus.yml
│   └── grafana-dashboard.json
│
├── mlruns/
├── dvc.yaml
├── params.yaml
├── requirements.txt
├── setup.py
└── README.md

```

---

## 2️⃣ Airflow DAG: `airflow/dags/data_pipeline.py`
- Task 1: Pull raw dataset from `data/raw/telecom_churn.csv`
- Task 2: Clean and preprocess dataset
- Task 3: Save processed dataset to `data/processed/churn_processed.csv`
- Optional: Trigger model training

Use **PythonOperator** for each task. Ensure DAG is **Docker-ready** and uses environment variables for dataset paths.

---

## 3️⃣ Model Training & Versioning
**File:** `src/models/train_model.py`  

- Load processed data
- Train **RandomForestClassifier** or **XGBoost** model
- Log metrics and parameters to **MLflow**
- Save model artifact to `models/churn_model.pkl`
- Track model & dataset with **DVC**
- Use `params.yaml` for hyperparameters

**File:** `src/models/predict_model.py`  
- Load trained model
- Provide a function that predicts churn probability from input features

---

## 4️⃣ Data Preprocessing
**File:** `src/data/preprocessing.py`  

- Include feature encoding, scaling, and missing value handling
- Must be reusable for both training and prediction

---

## 5️⃣ FastAPI Deployment
**File:** `deployment/app/main.py`  

- Create `/predict` POST endpoint
- Accept JSON input (customer features)
- Return churn probability
- Load model using MLflow or DVC
- Add `schemas.py` for Pydantic input validation

**Dockerfile:** Containerize the FastAPI app with Uvicorn.

---

## 6️⃣ CI/CD: GitHub Actions
**File:** `ci-cd/mlops_pipeline.yml`  

- Trigger: `push` to `main`
- Steps:
  1. Checkout code
  2. Setup Python environment
  3. Lint and run tests
  4. Build Docker images
  5. Push Docker images to AWS ECR
  6. Deploy to ECS Fargate
- Include environment variables for AWS credentials

---

## 7️⃣ Monitoring Placeholders
**Files:**
- `monitoring/prometheus.yml` — define scrape targets for FastAPI metrics
- `monitoring/grafana-dashboard.json` — sample dashboard with API latency, request count, and errors

---

## 8️⃣ Docker & Docker Compose
- Create `Dockerfile` for Airflow and FastAPI
- Optional `docker-compose.yml` to run Airflow + FastAPI locally

---

## 9️⃣ DVC & MLflow
- Initialize DVC and track datasets and models
- Configure MLflow to log experiments locally in `mlruns/`
- Enable easy reproduction of experiments

---

## 10️⃣ AWS Deployment Structure
- ECR: Store Docker images
- ECS Fargate: Container orchestration
- S3: Store raw & processed datasets, model artifacts
- Include instructions in `README.md` placeholders for credentials and deployment steps

---

## 11️⃣ Notebook
- `notebooks/churn_eda.ipynb`:
  - Exploratory Data Analysis
  - Feature correlations
  - Visualizations of churn patterns

---

## 12️⃣ Requirements
- Python 3.11+
- Packages:
  - airflow, pandas, scikit-learn, xgboost, mlflow, dvc, fastapi, uvicorn, pydantic, boto3, docker, prometheus-client

---

## 13️⃣ README.md
- Include project description, structure, setup, and usage instructions
- Include **links to Airflow, MLflow, FastAPI** documentation

---

### ✅ Instructions for Agent
- Generate **all code files with boilerplate** as described
- Ensure **all imports work**
- Use **production-ready code patterns**
- Make Docker images runnable
- Add **placeholders** for AWS credentials, S3 bucket names, and ECS configs
- Ensure reproducibility with **DVC + MLflow**

---
