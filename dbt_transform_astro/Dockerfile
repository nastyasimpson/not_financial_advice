FROM quay.io/astronomer/astro-runtime:12.7.1

WORKDIR /opt/airflow
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dags /opt/airflow/dags