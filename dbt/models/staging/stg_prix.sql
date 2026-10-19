SELECT ROUND(AVG(f.prix), 3) AS prix_moyen,
       COUNT(*) AS nb_prix
FROM marts.fait_prix f
JOIN marts.dim_station   s ON f.station_id = s.station_id
JOIN marts.dim_carburant c ON f.carburant  = c.carburant
JOIN marts.dim_date      d ON f.date_prix  = d.date_jour
WHERE c.carburant = 'GAZOLE'
  AND s.zone = 'Corse'
  AND d.est_weekend;