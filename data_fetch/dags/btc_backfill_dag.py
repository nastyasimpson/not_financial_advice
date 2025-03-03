from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Import the main function from your BTC script in data_ingestion/
from data_ingestion.fetch_btc_data import main as fetch_btc

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,  # Increased for robustness
    'retry_delay': timedelta(minutes=5),  # Wait 5 minutes between retries
}

with DAG(
    'btc_polygon_fetch',  # Keeping your original dag_id
    default_args=default_args,
    description='BTC price fetch pipeline from Polygon (incremental daily)',
    schedule_interval='@daily',
    start_date=datetime(2025, 2, 27),  # Updated to start from Feb 27 for real-time data
    catchup=False,
) as dag:
    fetch_btc_task = PythonOperator(
        task_id='fetch_btc_data',
        python_callable=fetch_btc,
        op_kwargs={'bulk': False, 'incremental': True, 'date': '{{ ds }}'},  # Match fetch_btc_data.py
    )