DROP TABLE IF EXISTS overtakes_debug;
CREATE TEMP TABLE overtakes_debug AS
SELECT DISTINCT
  overtaking_lap_times.lap,
  overtakes.lap AS lap_of_overtake,
  overtaking_drivers.full_name AS overtaking_name,
  overtaking_lap_times.position AS overtaking_pos,
  overtaken_drivers.full_name AS overtaken_name,
  overtaken_lap_times.position AS overtaken_pos,

  overtaking_lap_times.time AS overtaking_lap_time,
  overtaken_lap_times.time AS overtaken_lap_time,
  ROUND((overtaken_lap_times.seconds - overtaken_lap_stats.avg_seconds) / overtaken_lap_stats.stdev_seconds, 3) AS overtaken_sigmas,
  ROUND((overtaking_lap_times.running_milliseconds - overtaken_lap_times.running_milliseconds) / 1000, 3) AS gap,

  CASE
    WHEN overtakes.lap = overtaking_lap_times.lap THEN overtakes.overtake_desc
    WHEN overtaken_pit_stops.race_id IS NOT NULL THEN 'Pit Stop - ' || ROUND(overtaken_pit_stops.seconds, 3)
    ELSE NULL
  END AS event

FROM overtakes AS overtakes
  INNER JOIN races_ext AS races ON races.race_id = overtakes.race_id
  INNER JOIN circuits_ext AS circuits ON circuits.circuit_id = races.circuit_id

  INNER JOIN drivers AS overtaking_drivers ON overtaking_drivers.driver_id = overtakes.overtaking_driver_id
  INNER JOIN lap_times_ext AS overtaking_lap_times
    ON overtaking_lap_times.race_id = overtakes.race_id
    AND overtaking_lap_times.driver_id = overtaking_drivers.driver_id
    AND overtaking_lap_times.lap BETWEEN overtakes.lap - 2 AND overtakes.lap + 1
  INNER JOIN lap_time_stats AS overtaking_lap_stats
    ON overtaking_lap_stats.race_id = overtakes.race_id
    AND overtaking_lap_stats.driver_id = overtaking_drivers.driver_id

  INNER JOIN drivers AS overtaken_drivers ON overtaken_drivers.driver_id = overtakes.overtaken_driver_id
  INNER JOIN lap_times_ext AS overtaken_lap_times
    ON overtaken_lap_times.race_id = overtakes.race_id
    AND overtaken_lap_times.driver_id = overtaken_drivers.driver_id
    AND overtaken_lap_times.lap = overtaking_lap_times.lap
  INNER JOIN lap_time_stats AS overtaken_lap_stats
    ON overtaken_lap_stats.race_id = overtakes.race_id
    AND overtaken_lap_stats.driver_id = overtaken_drivers.driver_id
  LEFT JOIN pit_stops AS overtaken_pit_stops
    ON overtaken_pit_stops.race_id = overtakes.race_id
    AND overtaken_pit_stops.lap = overtaken_lap_times.lap
    AND overtaken_pit_stops.driver_id = overtaken_drivers.driver_id

  INNER JOIN results /*This is just here to be able to sort the drivers by their finishing position.*/
    ON results.race_id = overtakes.race_id
    AND results.driver_id = overtakes.overtaking_driver_id

WHERE
  races.year = 2021 AND circuits.country = 'Monaco' /*Set these values to the race you're interested in.*/
  /*AND overtakes.lap = 44 /*Set this value to have this look at all overtakes for a certain lap.*/
  /*AND overtaking_drivers.code = 'HAM' /*Set this value to look at overtakes for a specific driver.*/
  AND overtakes.overtake_type IN ('T', 'P', 'S') /*This should normally be left alone.*/
  AND overtakes.lap > 1 /*Exclude overtakes during the first lap, which are mostly overtakes from the start.*/

ORDER BY
  overtaking_drivers.full_name,
  overtakes.lap,
  overtaken_drivers.full_name,
  overtaking_lap_times.lap
;