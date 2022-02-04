DROP TABLE IF EXISTS drives_prelim;
CREATE TEMP TABLE drives_prelim AS
SELECT DISTINCT
  races.year,
  results.driver_id,
  races.round,
  results.constructor_id,
  COALESCE(NOT(results.constructor_id = LAG(results.constructor_id) OVER races_this_season), 1) AS is_first_race,
  COALESCE(NOT(results.constructor_id = LEAD(results.constructor_id) OVER races_this_season), 1) AS is_last_race

FROM results
  INNER JOIN races ON races.race_id = results.race_id

WINDOW
  races_this_season AS (
    PARTITION BY
      races.year,
      results.driver_id
    ORDER BY
      races.round ASC
  )
;

/*Cases where a driver is absent for one/more races and then returns TO THE SAME TEAM
are NOT counted as a separate drive! Only instances where a driver CHANGES TEAMS
midway through a season are counted as separate drives.*/
DROP TABLE IF EXISTS valid_drives;
CREATE TEMP TABLE valid_drives AS
SELECT DISTINCT
  races.year,
  results.driver_id,
  first_race.drive_id,
  first_race.constructor_id,
  first_race.round AS first_round,
  last_race.round AS last_round,
  first_race.round = first_round_driven.round AS is_first_drive_of_season,
  last_race.round = final_round_driven.round AS is_final_drive_of_season

FROM results
  INNER JOIN races ON races.race_id = results.race_id
  INNER JOIN (
    SELECT
      drives_prelim.*,
      RANK() OVER drive_number AS drive_id
    FROM drives_prelim
    WHERE is_first_race
    WINDOW drive_number AS (
      PARTITION BY year, driver_id
      ORDER BY round ASC
    )
  ) AS first_race
    ON first_race.year = races.year
    AND first_race.driver_id = results.driver_id

  INNER JOIN (
    SELECT
      drives_prelim.*,
      RANK() OVER drive_number AS drive_id
    FROM drives_prelim
    WHERE is_last_race
    WINDOW drive_number AS (
      PARTITION BY year, driver_id
      ORDER BY round ASC
    )
  ) AS last_race
    ON last_race.year = races.year
    AND last_race.driver_id = results.driver_id
    AND last_race.drive_id = first_race.drive_id

  INNER JOIN (
    SELECT
      year,
      driver_id,
      round
    FROM drives_prelim
    GROUP BY
      year,
      driver_id
    HAVING round = MIN(round)
  ) AS first_round_driven
    ON first_round_driven.year = races.year
    AND first_round_driven.driver_id = results.driver_id

  INNER JOIN (
    SELECT
      year,
      driver_id,
      round
    FROM drives_prelim
    GROUP BY
      year,
      driver_id
    HAVING round = MAX(round)
  ) AS final_round_driven
    ON final_round_driven.year = races.year
    AND final_round_driven.driver_id = results.driver_id

;

DROP TABLE IF EXISTS hiatus_prelim;
CREATE TEMP TABLE hiatus_prelim AS
SELECT DISTINCT
  races.year,
  driver_standings.driver_id,
  races.round,
  previous_results.constructor_id AS previous_constructor_id,
  next_results.constructor_id AS next_constructor_id,
  previous_results.constructor_id IS NOT NULL AS is_first_race,
  next_results.constructor_id IS NOT NULL AS is_last_race

FROM driver_standings_ext AS driver_standings
  INNER JOIN races_ext AS races ON races.race_id = driver_standings.race_id
  LEFT JOIN results
    ON results.race_id = driver_standings.race_id
    AND results.driver_id = driver_standings.driver_id

  LEFT JOIN races_ext AS previous_race
    ON previous_race.year = races.year
    AND previous_race.round = races.round - 1
  LEFT JOIN results AS previous_results
    ON previous_results.race_id = previous_race.race_id
    AND previous_results.driver_id = driver_standings.driver_id

  LEFT JOIN races_ext AS next_race
    ON next_race.year = races.year
    AND next_race.round = races.round + 1
  LEFT JOIN results AS next_results
    ON next_results.race_id = next_race.race_id
    AND next_results.driver_id = driver_standings.driver_id

WHERE
  results.driver_id IS NULL

;

DROP TABLE IF EXISTS hiatus_drives;
CREATE TEMP TABLE hiatus_drives AS
SELECT DISTINCT
  races.year,
  driver_standings.driver_id,
  -1 AS drive_id,
  -1 AS constructor_id,
  first_race.round AS first_round,
  last_race.round AS last_round,
  0 AS is_first_drive_of_season,
  0 AS is_final_drive_of_season

FROM driver_standings_ext AS driver_standings
  INNER JOIN races_ext AS races ON races.race_id = driver_standings.race_id
  LEFT JOIN results
    ON results.race_id = driver_standings.race_id
    AND results.driver_id = driver_standings.driver_id

  INNER JOIN (
    SELECT
      hiatus_prelim.*,
      RANK() OVER drive_number AS drive_id
    FROM hiatus_prelim
    WHERE is_first_race
    WINDOW drive_number AS (
      PARTITION BY year, driver_id
      ORDER BY round ASC
    )
  ) AS first_race
    ON first_race.year = races.year
    AND first_race.driver_id = driver_standings.driver_id

  INNER JOIN (
    SELECT
      hiatus_prelim.*,
      RANK() OVER drive_number AS drive_id
    FROM hiatus_prelim
    WHERE is_last_race
    WINDOW drive_number AS (
      PARTITION BY year, driver_id
      ORDER BY round ASC
    )
  ) AS last_race
    ON last_race.year = races.year
    AND last_race.driver_id = driver_standings.driver_id
    AND last_race.drive_id = first_race.drive_id

WHERE
  results.driver_id IS NULL
  AND NOT(first_race.previous_constructor_id = last_race.next_constructor_id)

;

DROP TABLE IF EXISTS drives;
CREATE TABLE drives AS
SELECT * FROM valid_drives
UNION ALL
SELECT * FROM hiatus_drives
;