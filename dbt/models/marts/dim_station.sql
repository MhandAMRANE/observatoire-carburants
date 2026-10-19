-- Dimension station : où le carburant est vendu

select
    station_id,
    adresse,
    ville,
    code_postal,
    code_departement,
    departement,
    region,
    zone,
    type_route,
    latitude,
    longitude
from {{ ref('stg_stations') }}