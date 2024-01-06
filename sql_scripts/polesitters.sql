DROP TABLE IF EXISTS polesitters;
CREATE TABLE polesitters AS
SELECT
  races.short_name,
  races.year,
  drivers.driver_id,
  drivers.full_name,
  CASE WHEN results.position = 1 THEN 1 ELSE 0 END AS won_from_pole

FROM lap_positions
  INNER JOIN drivers_ext AS drivers ON drivers.driver_id = lap_positions.driver_id
  INNER JOIN races_ext AS races ON races.race_id = lap_positions.race_id
  INNER JOIN results
    ON results.race_id = races.race_id
    AND results.driver_id = drivers.driver_id

WHERE
  lap_positions.lap = 0 /*Starting grid only*/
  AND lap_positions.position = 1 /*Pole-sitters only*/

ORDER BY
  races.year ASC,
  races.round ASC
;

DROP TABLE IF EXISTS polesitters_stats;
CREATE TABLE polesitters_stats AS
SELECT
  full_name AS driver_name,
  COUNT(*) AS num_poles,
  AVG(won_from_pole) AS pole_to_win_pct
FROM polesitters
GROUP BY driver_id
HAVING COUNT(*) >= 5
ORDER BY AVG(won_from_pole) ASC
;