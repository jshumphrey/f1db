/*This identifies all overtakes that take place during a race, and attempts to
classify those overtakes by how they occurred: the overtake occurred on track,
the overtake occurred because the overtaken driver made a pit stop, or the overtaken
driver retired from the race.

Keep in mind that the only data we have to detect and classify overtakes are: the position
of each driver _at the end of each lap_, the lap number and duration of any pit stops
a driver made, and the lap number on which a driver retired, if applicable. This means that
there are some very significant "blind spots" in terms of ability to detect overtakes.
Most notably, we have zero visibility to any situations where drivers overtake one another
back and forth within a single lap, because we can only look at the drivers' postions once per lap.

As a result, the query identifies overtakes as "situations where driver X is behind driver Y
this lap, but driver X was NOT behind driver Y last lap." Once those situations have been
identified (from cars_behind_this_lap and cars_behind_last_lap), the query attempts to categorize
them, according to the following logic:

1. If the overtaken driver retired on the lap on which he was overtaken,
   the overtake was due to a retirement.

2. If the overtaken driver pitted during the lap on which he was overtaken,
   the overtake was due to a pit stop, and the overtake occurred as the
   overtaken driver was entering the pit lane.

3. If the overtaken driver pitted during the lap prior to which he was overtaken,
   AND the gap (the "delta") between the overtaking driver and the overtaken driver
   was less than the duration of the overtaken driver's pit stop, the overtake
   was due to a pit stop, and the overtake occurred as the overtaken driver
   was exiting the pit lane.

4. If the overtake occurred on lap 1, and the drivers were within two grid positions
   one another, then the overtake occurred during the start of the race.
   (This is a pretty disgusting kludge, but it tends to work okay in practice.)

5. If none of the above situations apply, the overtake occurred on track.

*/

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
    WHEN pit_stops.milliseconds > overtaking_lap_times.running_milliseconds - overtaken_lap_times.running_milliseconds THEN 'P'
    WHEN lap_positions.lap = 1 AND (previous_lap.position - cars_behind_this_lap_results.grid) <= 2 THEN 'S'
    ELSE 'T'
  END AS overtake_type,
  CASE
    WHEN retirements.driver_id IS NOT NULL
    THEN retirements.retirement_type
    WHEN pit_stops.lap = lap_positions.lap
    THEN 'Pit Stop (Pit Entry)'
    WHEN pit_stops.milliseconds > overtaking_lap_times.running_milliseconds - overtaken_lap_times.running_milliseconds
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

  INNER JOIN lap_positions AS cars_behind_this_lap /*Join to ALL cars behind on this lap*/
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
