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

DROP TABLE IF EXISTS constructors_ext;
CREATE TABLE constructors_ext AS
SELECT DISTINCT
  constructors.*,
  COALESCE(short_constructor_names.short_name, constructors.name) AS short_name
FROM constructors
  LEFT JOIN short_constructor_names ON short_constructor_names.constructor_ref = constructors.constructor_ref
;

/*This adds "seconds" as a native field so it doesn't need to be recalculated,
and includes running totals of seconds and milliseconds.*/
DROP TABLE IF EXISTS lap_times_ext;
CREATE TABLE lap_times_ext AS
SELECT DISTINCT
  lap_times.*,
  SUM(milliseconds) OVER running_total AS running_milliseconds
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
  pit_stops.race_id IS NOT NULL AS is_pit_data_available,
  COALESCE(short_grand_prix_names.short_name, races.name) AS short_name
FROM races
  LEFT JOIN pit_stops ON pit_stops.race_id = races.race_id
  LEFT JOIN short_grand_prix_names ON short_grand_prix_names.full_name = races.name
;