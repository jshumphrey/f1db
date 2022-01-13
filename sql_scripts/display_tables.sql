DROP TABLE IF EXISTS overtakes_pretty;
CREATE TEMP TABLE overtakes_pretty AS
SELECT DISTINCT
  races.year,
  races.round,
  races.name AS race_name,
  overtakes.lap,
  overtaking_drivers.full_name AS overtaking_driver_name,
  overtakes.current_position,
  overtakes.previous_position,
  overtaken_drivers.full_name AS overtaken_driver_name,
  overtakes.overtake_type,
  overtakes.overtake_desc

FROM overtakes AS overtakes
  INNER JOIN drivers AS overtaking_drivers ON overtaking_drivers.driver_id = overtakes.overtaking_driver_id
  INNER JOIN drivers AS overtaken_drivers ON overtaken_drivers.driver_id = overtakes.overtaken_driver_id
  INNER JOIN races_ext AS races ON races.race_id = overtakes.race_id
  INNER JOIN circuits_ext AS circuits
    ON circuits.circuit_id = races.circuit_id
    AND circuits.last_race_year >= 2019
    AND circuits.number_of_races >= 5
  INNER JOIN results
    ON results.race_id = overtakes.race_id
    AND results.driver_id = overtakes.overtaking_driver_id

WHERE races.year = 2011 AND circuits.country = 'Canada'

ORDER BY
  races.year,
  races.round,
  overtakes.lap,
  results.position

;