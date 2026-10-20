"""
Pipeline quotidien de l'observatoire des prix des carburants :
1. extraire les prix depuis l'API et les charger dans PostgreSQL (schéma raw)
2. construire le schéma en étoile et lancer les tests de qualité avec dbt
"""

from datetime import datetime

from airflow.sdk import dag
from airflow.providers.standard.operators.bash import BashOperator

# Chemins dans le conteneur Airflow
VENV = "/opt/airflow/pipeline_venv/bin"   # environnement Python du pipeline
PROJET = "/opt/projet"                     # code partagé depuis le PC


@dag(
    dag_id="pipeline_carburants",
    schedule=None,
    start_date=datetime(2026, 10, 1),
    catchup=False,
    tags=["carburants"],
)
def pipeline_carburants():

    extraire_prix = BashOperator(
        task_id="extraire_prix",
        bash_command=f"{VENV}/python {PROJET}/extract/extract_prix.py",
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            f"{VENV}/dbt build "
            f"--project-dir {PROJET}/dbt "
            f"--profiles-dir {PROJET}/dbt"
        ),
    )

    extraire_prix >> dbt_build


pipeline_carburants()