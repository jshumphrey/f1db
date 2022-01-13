DROP TABLE IF EXISTS overtakes;
CREATE TABLE overtakes AS
SELECT DISTINCT
  lap_positions.race_id,
  lap_positions.driver_id AS overtaking_driver_id,
  lap_positions.lap,
  lap_positions.position AS current_position,
  previous_lap.position AS previous_position,
  cars_behind_this_lap.driver_id AS overtaken_driver_id,
  CASE
    WHEN retirements.driver_id IS NOT NULL THEN 'R'
    WHEN pit_stops.lap = lap_positions.lap THEN 'P'
    WHEN pit_stops.seconds > overtaking_lap_times.running_seconds - overtaken_lap_times.running_seconds THEN 'P'
    WHEN lap_positions.lap = 1 AND (previous_lap.position - cars_behind_this_lap_results.grid) <= 2 THEN 'S'
    ELSE 'T'
  END AS overtake_type,
  CASE
    WHEN retirements.driver_id IS NOT NULL
    THEN retirements.retirement_type
    WHEN pit_stops.lap = lap_positions.lap
    THEN 'Pit Stop (Pit Entry)'
    WHEN pit_stops.seconds > overtaking_lap_times.running_seconds - overtaken_lap_times.running_seconds
    THEN 'Pit Stop (Pit Exit)'
    WHEN lap_positions.lap = 1 AND (previous_lap.position - cars_behind_this_lap_results.grid) <= 2
    THEN 'Start'
    ELSE 'Track'
  END AS overtake_desc

FROM lap_positions
  INNER JOIN races_ext AS races
    ON races.race_id = lap_positions.race_id
    AND races.is_pit_data_available = 1
  INNER JOIN lap_positions AS previous_lap
    ON previous_lap.race_id = lap_positions.race_id
    AND previous_lap.driver_id = lap_positions.driver_id
    AND previous_lap.lap = lap_positions.lap - 1

  INNER JOIN lap_positions AS cars_behind_this_lap /*Cross join to ALL cars behind on this lap*/
    ON cars_behind_this_lap.race_id = lap_positions.race_id
    AND cars_behind_this_lap.lap = lap_positions.lap
    AND cars_behind_this_lap.position > lap_positions.position
  LEFT JOIN results AS cars_behind_this_lap_results
    ON cars_behind_this_lap_results.race_id = lap_positions.race_id
    AND cars_behind_this_lap_results.driver_id = cars_behind_this_lap.driver_id
  LEFT JOIN lap_positions AS cars_behind_last_lap
    ON cars_behind_last_lap.race_id = lap_positions.race_id
    AND cars_behind_last_lap.lap = lap_positions.lap - 1
    AND cars_behind_last_lap.driver_id = cars_behind_this_lap.driver_id /*NOT lap_positions.driver_id!!!!!!*/
    AND cars_behind_last_lap.position > previous_lap.position

  LEFT JOIN retirements
    ON retirements.race_id = lap_positions.race_id
    AND retirements.lap = lap_positions.lap
    AND retirements.driver_id = cars_behind_this_lap.driver_id

  LEFT JOIN pit_stops AS pit_stops
    ON pit_stops.race_id = lap_positions.race_id
    AND pit_stops.lap BETWEEN lap_positions.lap - 1 AND lap_positions.lap /*This lets us bring in pit stops from the "previous" lap*/
    AND pit_stops.driver_id = cars_behind_this_lap.driver_id
  LEFT JOIN lap_times_ext AS overtaking_lap_times
    ON overtaking_lap_times.race_id = lap_positions.race_id
    AND overtaking_lap_times.driver_id = lap_positions.driver_id
    AND overtaking_lap_times.lap = pit_stops.lap - 1
  LEFT JOIN lap_times_ext AS overtaken_lap_times
    ON overtaken_lap_times.race_id = lap_positions.race_id
    AND overtaken_lap_times.driver_id = pit_stops.driver_id
    AND overtaken_lap_times.lap = pit_stops.lap - 1

WHERE
  cars_behind_last_lap.driver_id IS NULL /*The car was NOT behind last lap (but is behind this lap due to the INNER JOIN)*/

ORDER BY
  lap_positions.race_id,
  lap_positions.lap,
  lap_positions.position

;
