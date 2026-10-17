"""
Extraction des prix des carburants en France (flux instantané v2).

Étapes :
    1. Télécharge le flux JSON publié sur data.economie.gouv.fr
    2. Sauvegarde le fichier brut dans data/raw/ (horodaté)
    3. Transforme les données : une ligne par station et par carburant
    4. Charge les stations et les prix dans PostgreSQL (schéma "raw")

Usage :
    python extract/extract_prix.py              # pipeline complet
    python extract/extract_prix.py --no-load    # sans chargement en base
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

API_URL = (
    "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "prix-des-carburants-en-france-flux-instantane-v2/exports/json"
)

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Carburants publiés dans le flux : chacun a une colonne <nom>_prix et <nom>_maj
CARBURANTS = ["gazole", "sp95", "sp98", "e10", "e85", "gplc"]

COLONNES_STATION = {
    "id": "station_id",
    "adresse": "adresse",
    "ville": "ville",
    "cp": "code_postal",
    "code_departement": "code_departement",
    "departement": "departement",
    "region": "region",
    "pop": "type_route",          # "R" = route, "A" = autoroute
    "latitude": "latitude",
    "longitude": "longitude",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("extract_prix")


# ---------------------------------------------------------------------------
# 1. Extraction
# ---------------------------------------------------------------------------
def telecharger_flux(url: str = API_URL, timeout: int = 120) -> list[dict]:
    """Télécharge le flux complet et renvoie la liste des stations."""
    log.info("Téléchargement du flux : %s", url)
    reponse = requests.get(url, timeout=timeout)
    reponse.raise_for_status()
    donnees = reponse.json()
    log.info("%d stations reçues", len(donnees))
    return donnees


def sauvegarder_brut(donnees: list[dict], dossier: Path = RAW_DIR) -> Path:
    """Sauvegarde le JSON brut, horodaté, pour pouvoir rejouer le pipeline."""
    dossier.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    chemin = dossier / f"prix_carburants_{horodatage}.json"
    chemin.write_text(json.dumps(donnees, ensure_ascii=False), encoding="utf-8")
    log.info("Fichier brut sauvegardé : %s", chemin)
    return chemin


# ---------------------------------------------------------------------------
# 2. Transformation
# ---------------------------------------------------------------------------
def _corriger_coordonnee(valeur) -> float | None:
    """Le flux publie parfois les coordonnées multipliées par 100 000."""
    try:
        v = float(valeur)
    except (TypeError, ValueError):
        return None
    return v / 100_000 if abs(v) > 180 else v


def extraire_stations(donnees: list[dict]) -> pd.DataFrame:
    """Une ligne par station, avec ses informations descriptives."""
    df = pd.DataFrame(donnees)

    manquantes = [c for c in COLONNES_STATION if c not in df.columns]
    if manquantes:
        log.warning("Colonnes absentes du flux : %s", manquantes)

    presentes = {k: v for k, v in COLONNES_STATION.items() if k in df.columns}
    stations = df[list(presentes)].rename(columns=presentes)

    for col in ("latitude", "longitude"):
        if col in stations:
            stations[col] = stations[col].map(_corriger_coordonnee)

    stations["station_id"] = stations["station_id"].astype(str)
    return stations.drop_duplicates(subset="station_id")


def extraire_prix(donnees: list[dict]) -> pd.DataFrame:
    """
    Passe du format "large" (une colonne par carburant)
    au format "long" : station_id | carburant | prix | date_maj.
    """
    df = pd.DataFrame(donnees)
    lignes = []

    for carburant in CARBURANTS:
        col_prix, col_maj = f"{carburant}_prix", f"{carburant}_maj"
        if col_prix not in df.columns:
            log.warning("Carburant absent du flux : %s", carburant)
            continue

        sous_df = pd.DataFrame({
            "station_id": df["id"].astype(str),
            "carburant": carburant.upper(),
            "prix": pd.to_numeric(df[col_prix], errors="coerce"),
            "date_maj": pd.to_datetime(df.get(col_maj), errors="coerce", utc=True),
        })
        lignes.append(sous_df)

    if not lignes:
        return pd.DataFrame(columns=["station_id", "carburant", "prix", "date_maj"])

    prix = pd.concat(lignes, ignore_index=True)

    # Règles de qualité minimales : prix renseigné, positif et réaliste
    avant = len(prix)
    prix = prix.dropna(subset=["prix", "date_maj"])
    prix = prix[(prix["prix"] > 0.5) & (prix["prix"] < 5)]
    log.info("Prix valides : %d / %d lignes", len(prix), avant)

    prix["date_extraction"] = datetime.now(timezone.utc)
    return prix.drop_duplicates(subset=["station_id", "carburant", "date_maj"])


# ---------------------------------------------------------------------------
# 3. Chargement
# ---------------------------------------------------------------------------
def url_base() -> str:
    return (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER', 'carburants')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'carburants')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'carburants')}"
    )


def charger(stations: pd.DataFrame, prix: pd.DataFrame) -> None:
    """
    Charge dans des tables temporaires puis fusionne (upsert) :
    relancer le script plusieurs fois ne crée pas de doublons.
    """
    engine = create_engine(url_base())

    with engine.begin() as conn:
        stations.to_sql("_tmp_stations", conn, schema="raw", if_exists="replace", index=False)
        prix.to_sql("_tmp_prix", conn, schema="raw", if_exists="replace", index=False)

        conn.execute(text("""
            INSERT INTO raw.stations AS s
                (station_id, adresse, ville, code_postal, code_departement,
                 departement, region, type_route, latitude, longitude)
            SELECT station_id, adresse, ville, code_postal, code_departement,
                   departement, region, type_route, latitude, longitude
            FROM raw._tmp_stations
            ON CONFLICT (station_id) DO UPDATE SET
                adresse = EXCLUDED.adresse,
                ville = EXCLUDED.ville,
                code_postal = EXCLUDED.code_postal,
                code_departement = EXCLUDED.code_departement,
                departement = EXCLUDED.departement,
                region = EXCLUDED.region,
                type_route = EXCLUDED.type_route,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                derniere_vue = NOW();
        """))

        resultat = conn.execute(text("""
            INSERT INTO raw.prix_carburants
                (station_id, carburant, prix, date_maj, date_extraction)
            SELECT station_id, carburant, prix, date_maj, date_extraction
            FROM raw._tmp_prix
            ON CONFLICT (station_id, carburant, date_maj) DO NOTHING;
        """))

        conn.execute(text("DROP TABLE raw._tmp_stations, raw._tmp_prix;"))

    log.info("%d stations mises à jour, %d nouveaux prix insérés",
             len(stations), resultat.rowcount)


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-load", action="store_true",
                        help="Télécharger et transformer sans charger en base")
    args = parser.parse_args()

    donnees = telecharger_flux()
    sauvegarder_brut(donnees)

    stations = extraire_stations(donnees)
    prix = extraire_prix(donnees)
    log.info("%d stations, %d prix après transformation", len(stations), len(prix))

    if args.no_load:
        print(prix.head(10).to_string(index=False))
        return

    charger(stations, prix)


if __name__ == "__main__":
    main()
