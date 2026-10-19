-- Dimension carburant : la liste de référence des carburants

select
    carburant,
    libelle,
    famille
from {{ ref('carburants') }}