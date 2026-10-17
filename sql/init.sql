-- Exécuté automatiquement au premier démarrage du conteneur PostgreSQL.
-- Couche "raw" : données telles qu'elles arrivent du flux, après un nettoyage minimal.
-- Les couches "staging" et "marts" seront construites ensuite avec dbt.

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.stations (
    station_id        TEXT PRIMARY KEY,
    adresse           TEXT,
    ville             TEXT,
    code_postal       TEXT,
    code_departement  TEXT,
    departement       TEXT,
    region            TEXT,
    type_route        TEXT,             -- R = route, A = autoroute
    latitude          DOUBLE PRECISION,
    longitude         DOUBLE PRECISION,
    premiere_vue      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    derniere_vue      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.prix_carburants (
    station_id        TEXT        NOT NULL REFERENCES raw.stations (station_id),
    carburant         TEXT        NOT NULL,
    prix              NUMERIC(5,3) NOT NULL CHECK (prix > 0),
    date_maj          TIMESTAMPTZ NOT NULL,   -- date de mise à jour du prix par la station
    date_extraction   TIMESTAMPTZ NOT NULL,   -- date à laquelle notre pipeline l'a récupéré
    PRIMARY KEY (station_id, carburant, date_maj)
);

CREATE INDEX IF NOT EXISTS idx_prix_date ON raw.prix_carburants (date_maj);
CREATE INDEX IF NOT EXISTS idx_prix_carburant ON raw.prix_carburants (carburant);
