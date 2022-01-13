DROP TABLE IF EXISTS circuits_ext;
CREATE TABLE circuits_ext AS
SELECT DISTINCT
  circuits.*,
  MAX(races.year) AS last_race_year,
  COUNT(DISTINCT races.race_id) AS number_of_races
FROM circuits
  INNER JOIN races ON races.circuit_id = circuits.circuit_id
GROUP BY circuits.circuit_id
;

/*This adds "seconds" as a native field so it doesn't need to be recalculated,
and includes running totals of seconds and milliseconds.*/
DROP TABLE IF EXISTS lap_times_ext;
CREATE TABLE lap_times_ext AS
SELECT DISTINCT
  lap_times.*,
  SUM(milliseconds) OVER running_total AS running_milliseconds,
  SUM(seconds) OVER running_total AS running_seconds,
  STRFTIME('%H:%M:%f', 'NOW', 'START OF DAY', '+' || SUM(seconds) OVER running_total || ' SECONDS') AS running_time_str
FROM lap_times
WINDOW
  running_total AS (
    PARTITION BY race_id,  driver_id
    ORDER BY race_id, driver_id, lap
    ROWS UNBOUNDED PRECEDING
  )
ORDER BY
  race_id,
  driver_id,
  lap
;

DROP TABLE IF EXISTS lap_time_stats;
CREATE TABLE lap_time_stats AS
SELECT
  lap_times.race_id,
  lap_times.driver_id,
  AVG(milliseconds) AS avg_milliseconds,
  AVG(seconds) AS avg_seconds,
  STDEV_POP(milliseconds) AS stdev_milliseconds,
  STDEV_POP(seconds) AS stdev_seconds
FROM lap_times_ext AS lap_times
GROUP BY
  lap_times.race_id,
  lap_times.driver_id
;

DROP TABLE IF EXISTS races_ext;
CREATE TABLE races_ext AS
SELECT DISTINCT
  races.*,
  pit_stops.race_id IS NOT NULL AS is_pit_data_available
FROM races
  LEFT JOIN pit_stops ON pit_stops.race_id = races.race_id
;
