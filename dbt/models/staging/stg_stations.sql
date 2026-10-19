-- Modèle staging des stations :
-- nettoie les textes et ajoute des colonnes lisibles pour l'analyse.

select
    -- Identifiant : inchangé
    station_id,

    -- Textes nettoyés
    trim(adresse)                     as adresse,
    initcap(trim(ville))              as ville,
    code_postal,
    upper(code_departement)           as code_departement,
    departement,
    region,

    -- Nouvelle colonne : Corse ou Continent
    case
        when upper(code_departement) in ('2A', '2B') then 'Corse'
        else 'Continent'
    end                               as zone,

    -- Code de route traduit en texte lisible
    case type_route
        when 'A' then 'Autoroute'
        when 'R' then 'Route'
        else 'Inconnu'
    end                               as type_route,

    -- Coordonnées GPS : inchangées
    latitude,
    longitude

from {{ source('raw', 'stations') }}