/*This table identifies any cases where a driver retires from a race.

I'd much prefer to set the retirement type by using status.status_id
instead of relying on the hardcoded status strings, but the API developer
has said that any integer ID values (on ANY table) are subject to change.*/
DROP TABLE IF EXISTS retirements;
CREATE TABLE retirements AS
SELECT DISTINCT
  results.race_id,
  results.driver_id,
  results.laps + 1 AS lap /*It's during the x+1th lap that they actually retired*/,
  results.position_order, /*This yields the position they dropped to after retiring*/
  results.status_id,
  'Retirement (' || CASE
    WHEN status.status IN ('Disqualified') THEN 'Disqualification'
    WHEN status.status IN ('Accident', 'Collision', 'Spun off') THEN 'Driver Error'
    ELSE 'Mechanical Problem'
  END || ')' AS retirement_type
FROM results
  LEFT JOIN drivers ON drivers.driver_id = results.driver_id
  INNER JOIN status
    ON status.status_id = results.status_id
    AND status.status_id > 1 /*Excludes drivers that finished the race*/
    AND NOT(SUBSTR(status.status, 1, 1) = "+") /*Excludes "+X Lap(s)"*/
;