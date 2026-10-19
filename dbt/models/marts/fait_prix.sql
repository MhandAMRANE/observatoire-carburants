{{
    config(
        materialized = 'incremental',
        unique_key = ['station_id', 'carburant', 'date_maj']
    )
}}
-- Table de faits : un prix par station, carburant et date de mise à jour

select
    p.station_id,
    p.carburant,
    p.date_prix,
    p.date_maj,
    p.prix,
    p.date_extraction

from {{ ref('stg_prix') }} p

-- On garde seulement les prix rattachés à une station et à un carburant connus
inner join {{ ref('stg_stations') }} s on p.station_id = s.station_id
inner join {{ ref('carburants') }}   c on p.carburant  = c.carburant

{% if is_incremental() %}
-- Exécutions suivantes : seulement les prix chargés depuis la dernière fois
where p.date_extraction > (select max(date_extraction) from {{ this }})
{% endif %}