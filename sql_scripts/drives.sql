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
DROP TABLE IF EXISTS drives;
CREATE TABLE drives AS
SELECT DISTINCT
  races.year,
  results.driver_id,
  first_race.drive_id,
  first_race.constructor_id,
  first_race.round AS first_round,
  last_race.round AS last_round

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

;