"""Tests unitaires de la transformation (sans réseau ni base de données)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "extract"))

from extract_prix import _corriger_coordonnee, extraire_prix, extraire_stations  # noqa: E402

ECHANTILLON = [
    {
        "id": 20000001, "adresse": "Route de Bastia", "ville": "Ajaccio", "cp": "20000",
        "code_departement": "2A", "departement": "Corse-du-Sud", "region": "Corse",
        "pop": "R", "latitude": "4192600", "longitude": "872100",
        "gazole_prix": 1.899, "gazole_maj": "2026-10-17T08:15:00+02:00",
        "sp95_prix": 1.959, "sp95_maj": "2026-10-17T08:15:00+02:00",
        "e85_prix": None, "e85_maj": None,
    },
    {
        "id": 75000002, "adresse": "Quai de la Seine", "ville": "Paris", "cp": "75019",
        "code_departement": "75", "departement": "Paris", "region": "Île-de-France",
        "pop": "R", "latitude": 48.88, "longitude": 2.37,
        "gazole_prix": 9.99,                       # prix aberrant -> doit être exclu
        "gazole_maj": "2026-10-17T09:00:00+02:00",
        "sp95_prix": 1.799, "sp95_maj": "2026-10-17T09:00:00+02:00",
        "e85_prix": 0.899, "e85_maj": "2026-10-16T18:00:00+02:00",
    },
]


def test_format_long():
    prix = extraire_prix(ECHANTILLON)
    assert set(prix.columns) >= {"station_id", "carburant", "prix", "date_maj"}
    # Ajaccio : gazole + sp95 ; Paris : sp95 + e85 (gazole aberrant exclu)
    assert len(prix) == 4


def test_prix_aberrants_et_vides_exclus():
    prix = extraire_prix(ECHANTILLON)
    assert prix["prix"].between(0.5, 5).all()
    assert prix["prix"].notna().all()


def test_stations_uniques_et_coordonnees():
    stations = extraire_stations(ECHANTILLON + ECHANTILLON[:1])  # doublon volontaire
    assert stations["station_id"].is_unique
    ajaccio = stations.set_index("station_id").loc["20000001"]
    assert abs(ajaccio["latitude"] - 41.926) < 0.001


def test_corriger_coordonnee():
    assert _corriger_coordonnee("4892600") == 48.926
    assert _corriger_coordonnee(2.35) == 2.35
    assert _corriger_coordonnee(None) is None
