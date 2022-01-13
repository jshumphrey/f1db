DROP TABLE IF EXISTS overtakes_by_circuit;
CREATE TEMP TABLE overtakes_by_circuit AS
SELECT DISTINCT
  circuits.circuit_id,
  circuits.name AS circuit_name,
  races.year,
  races.name AS race_name,
  CASE
    WHEN overtakes.overtake_type = 'T' THEN 'Track'
    WHEN overtakes.overtake_type = 'P' THEN 'Pit'
  END AS overtake_type,
  COALESCE(COUNT(overtakes.race_id), 0) AS num_overtakes

FROM circuits_ext AS circuits
  INNER JOIN races_ext AS races
    ON races.circuit_id = circuits.circuit_id
    AND races.is_pit_data_available = 1
  LEFT JOIN overtakes
    ON overtakes.race_id = races.race_id
    AND overtakes.overtake_type IN ('T', 'P')

WHERE
  circuits.last_race_year >= 2019
  AND circuits.number_of_races >= 5

GROUP BY
  circuits.circuit_id,
  races.race_id,
  overtakes.overtake_type

ORDER BY
  circuits.name,
  races.year,
  overtakes.overtake_type

;
