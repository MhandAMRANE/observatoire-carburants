-- Test : aucun prix ne doit sortir de la fourchette réaliste.
-- Le test réussit si cette requête ne renvoie aucune ligne.

select *
from {{ ref('fait_prix') }}
where prix < 0.5
   or prix > 5