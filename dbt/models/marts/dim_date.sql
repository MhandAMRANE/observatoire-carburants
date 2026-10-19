-- Dimension date : un jour par ligne, du premier au dernier prix collecté

-- Étape 1 : trouver la première et la dernière date des prix
with bornes as (
    select
        min(date_prix) as date_min,
        max(date_prix) as date_max
    from {{ ref('stg_prix') }}
),

-- Étape 2 : générer une ligne par jour entre ces deux dates
jours as (
    select generate_series(date_min, date_max, interval '1 day')::date as date_jour
    from bornes
)

-- Étape 3 : calculer les informations de chaque jour
select
    date_jour,
    extract(year from date_jour)::int     as annee,
    extract(month from date_jour)::int    as mois,
    extract(day from date_jour)::int      as jour,
    extract(isodow from date_jour)::int   as jour_semaine,

    case extract(isodow from date_jour)::int
        when 1 then 'Lundi'
        when 2 then 'Mardi'
        when 3 then 'Mercredi'
        when 4 then 'Jeudi'
        when 5 then 'Vendredi'
        when 6 then 'Samedi'
        else 'Dimanche'
    end                                   as nom_jour,

    extract(isodow from date_jour) in (6, 7) as est_weekend

from jours