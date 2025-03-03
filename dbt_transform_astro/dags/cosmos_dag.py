from cosmos import DbtDag, ProjectConfig, ProfileConfig, ExecutionConfig
from cosmos.config import ExecutionMode
from cosmos.profiles import SnowflakeUserPasswordProfileMapping
from datetime import datetime

# Configure profile for Snowflake
profile_config = ProfileConfig(
    profile_name="trust_score_pipeline",
    target_name="dev",
    profile_mapping=SnowflakeUserPasswordProfileMapping(
        conn_id="snowflake_conn",
        profile_args={"schema": "RAW"},
    ),
)

# Configure dbt project
project_config = ProjectConfig(
    dbt_project_path="/opt/airflow/dags/dbt_trust_score",  # Updated path for Astro runtime
)

# Configure execution (use VIRTUALENV mode, remove specific dbt_executable_path)
execution_config = ExecutionConfig(
    execution_mode=ExecutionMode.VIRTUALENV,  # Use enum value for astronomer-cosmos
    dbt_executable_path=None,  # Remove specific path, let astronomer-cosmos find dbt globally via requirements.txt
)

# Create the DAG
cosmos_dag = DbtDag(
    project_config=project_config,
    profile_config=profile_config,
    execution_config=execution_config,
    operator_args={
        "install_deps": True,
        "full_refresh": False,
    },
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    dag_id="trust_score_dbt_dag",
    default_args={"retries": 2},
)