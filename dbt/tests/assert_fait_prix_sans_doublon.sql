-- Test : un prix ne doit apparaître qu'une fois
-- pour une même station, un même carburant et une même mise à jour.

select station_id, carburant, date_maj, count(*) as nb
from {{ ref('fait_prix') }}
group by station_id, carburant, date_maj
having count(*) > 1