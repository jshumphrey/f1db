/*This table extends and unifies the lap_times and qualifying tables.

It includes a record for a fake "qualifying" lap for any driver that did not qualify
(or did not participate in qualifying, or was excluded from qualifying), and it includes
a record for the lap in which a driver retires (lap_times will not have this lap because
the driver did not complete the lap).

In both of these cases, the missing data can cause code that expects a record for every
"lap" of the race to do strange things, so this table mocks up some records
that allows code to handle them in a stable fashion.*/
DROP TABLE IF EXISTS lap_positions;
CREATE TABLE lap_positions AS
SELECT DISTINCT /*Normal race*/
  race_id,
  driver_id,
  lap,
  position,
  'Race' AS lap_type
FROM lap_times

UNION ALL

SELECT DISTINCT /*Lap 0 - i.e. starting grid*/
  results.race_id,
  results.driver_id,
  0 AS lap,
  results.grid,
  CASE
    WHEN qualifying.race_id IS NULL THEN 'Starting Position - No Qualification'
    WHEN qualifying.position < results.grid THEN 'Starting Position - Grid Drop'
    WHEN qualifying.position > results.grid THEN 'Starting Position - Grid Increase'
    ELSE 'Starting Position - Qualifying'
  END AS lap_type
FROM results
  LEFT JOIN qualifying
    ON qualifying.race_id = results.race_id
    AND qualifying.driver_id = results.driver_id

UNION ALL

SELECT DISTINCT /*Retirement*/
  race_id,
  driver_id,
  lap,
  position_order AS position,
  retirement_type AS lap_type
FROM retirements

ORDER BY
  race_id,
  driver_id,
  lap,
  position

;