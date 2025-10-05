FROM apache/airflow:2.9.2-python3.11

USER root
WORKDIR /opt/airflow

COPY airflow/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY airflow/dags/ /opt/airflow/dags/
COPY src/ /opt/airflow/src/
COPY params.yaml /opt/airflow/params.yaml
COPY data/raw/ /opt/airflow/data/raw/

ENV PYTHONPATH="/opt/airflow"

USER airflow
