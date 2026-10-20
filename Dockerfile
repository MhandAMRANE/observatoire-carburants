# On part de l'image officielle d'Airflow
FROM apache/airflow:3.3.2

# On copie la liste de nos bibliothèques dans l'image
COPY requirements.txt /tmp/requirements.txt

# On crée un environnement Python séparé et on y installe nos bibliothèques
RUN python -m venv /opt/airflow/pipeline_venv \
    && /opt/airflow/pipeline_venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt