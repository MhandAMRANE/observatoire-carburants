
from datetime import datetime

from airflow.sdk import dag
from airflow.providers.standard.operators.bash import BashOperator


@dag(
    dag_id="premier_dag",
    schedule=None,
    start_date=datetime(2026, 10, 1),
    catchup=False,
    tags=["apprentissage"],
)
def premier_dag():

    dire_bonjour = BashOperator(
        task_id="dire_bonjour",
        bash_command="echo 'Bonjour depuis Airflow !'",
    )

    afficher_date = BashOperator(
        task_id="afficher_date",
        bash_command="date",
    )

    dire_bonjour >> afficher_date


premier_dag()