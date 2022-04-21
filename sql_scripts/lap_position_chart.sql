DROP TABLE IF EXISTS lap_position_chart;
CREATE TEMP TABLE lap_position_chart AS
SELECT DISTINCT
  races.race_id,
  races.year,
  races.round,
  races.name AS race_name,
  races.short_name AS race_short_name,

  drivers.driver_id,
  drivers.full_name,
  drivers.surname,
  drivers.code,
  constructors.constructor_id,
  constructors.short_name AS constructor_name,
  liveries.primary_hex_code AS hex_code,
  team_driver_ranks.team_driver_rank,
  DENSE_RANK() OVER legend_rank AS legend_rank,

  lap_positions.lap,
  lap_positions.position,
  LAG(lap_positions.position) OVER driver_positions AS previous_lap_position,
  CASE
    WHEN retirements.driver_id IS NOT NULL THEN "Retired"
    WHEN pit_stops.driver_id IS NOT NULL THEN "Pitted"
    ELSE "Normal"
  END AS marker_type

FROM lap_positions
  INNER JOIN races_ext AS races ON races.race_id = lap_positions.race_id
  INNER JOIN results
    ON results.race_id = races.race_id
    AND results.driver_id = lap_positions.driver_id

  INNER JOIN drivers_ext AS drivers ON drivers.driver_id = lap_positions.driver_id
  LEFT JOIN constructors_ext AS constructors ON constructors.constructor_id = results.constructor_id
  LEFT JOIN liveries
    ON liveries.constructor_ref = constructors.constructor_ref
    AND races.year BETWEEN liveries.start_year AND COALESCE(liveries.end_year, 9999)
  LEFT JOIN team_driver_ranks
    ON team_driver_ranks.year = races.year
    AND team_driver_ranks.constructor_id = constructors.constructor_id
    AND team_driver_ranks.driver_id = drivers.driver_id

  LEFT JOIN pit_stops
    ON pit_stops.race_id = lap_positions.race_id
    AND pit_stops.lap = lap_positions.lap
    AND pit_stops.driver_id = lap_positions.driver_id
  LEFT JOIN retirements
    ON retirements.race_id = lap_positions.race_id
    AND retirements.lap = lap_positions.lap
    AND retirements.driver_id = lap_positions.driver_id

WHERE
  lap_positions.race_id = $race_id

WINDOW
  legend_rank AS (
    PARTITION BY
      lap_positions.lap
    ORDER BY
      liveries.primary_hex_code,
      team_driver_ranks.team_driver_rank
  ),

  driver_positions AS (
    PARTITION BY
      lap_positions.driver_id
    ORDER BY
      lap_positions.lap ASC
  )

ORDER BY
  lap_positions.lap,
  drivers.surname,
  drivers.full_name
;