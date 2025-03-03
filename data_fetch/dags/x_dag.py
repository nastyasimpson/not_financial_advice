from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

# Import the main function from your X script in data_ingestion/
from data_ingestion.fetch_and_analyze_x_bulk_feb import main as fetch_analyze_x  # Adjust if using fetch_and_analyze_x.py

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,  # Increased for robustness
    'retry_delay': timedelta(minutes=5),  # Wait 5 minutes between retries
}

with DAG(
    'x_fetch',  # Unique dag_id for X pipeline
    default_args=default_args,
    description='X influencer sentiment pipeline',
    schedule_interval='@daily',
    start_date=datetime(2025, 2, 27),  # Updated to start from Feb 27 for real-time data
    catchup=False,
) as dag:
    fetch_x_task = PythonOperator(
        task_id='fetch_analyze_x_data',
        python_callable=fetch_analyze_x,
        op_kwargs={'bulk': False, 'incremental': True, 'date': '{{ ds }}'},  # Incremental X data
    )