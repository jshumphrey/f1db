DROP TABLE IF EXISTS driver_max_points;
CREATE TEMP TABLE driver_max_points AS
SELECT DISTINCT
  driver_standings.driver_id,
  driver_standings.points AS current_points,
  driver_standings.position AS current_position,
  driver_standings.points + COALESCE(next_race.max_points, 0) AS max_points_next_race,
  driver_standings.points + COALESCE(SUM(upcoming_races.max_points), 0) AS max_points_this_season

FROM driver_standings_ext AS driver_standings
  INNER JOIN races_ext AS races ON races.race_id = driver_standings.race_id
  LEFT JOIN races_ext AS next_race
    ON next_race.year = races.year
    AND next_race.round = races.round + 1
  LEFT JOIN races_ext AS upcoming_races
    ON upcoming_races.year = races.year
    AND upcoming_races.round > races.round

WHERE
  driver_standings.race_id = $race_id

GROUP BY
  driver_standings.driver_id

;

DROP TABLE IF EXISTS delta_standings_boxplot;
CREATE TEMP TABLE delta_standings_boxplot AS
SELECT DISTINCT
  races.year,
  races.round,
  races.race_id,
  races.name AS race_name,
  races.short_name AS race_short_name,
  drivers.driver_id,
  drivers.full_name,
  drivers.surname,
  drivers.code,
  COALESCE(constructors.constructor_id, 0) AS constructor_id,
  COALESCE(constructors.short_name, "Hiatus") AS constructor_name,
  COALESCE(liveries.primary_hex_code, "#000000") AS hex_code,

  driver_standings.points AS current_points,
  driver_standings.position AS current_position,
  driver_max_points.max_points_next_race,
  driver_max_points.max_points_this_season,
  best_positions.best_position_next_race,
  best_positions.best_position_this_season,
  worst_positions.worst_position_next_race,
  worst_positions.worst_position_this_season

FROM drivers_ext AS drivers
  INNER JOIN driver_standings_ext AS driver_standings ON driver_standings.driver_id = drivers.driver_id
  INNER JOIN driver_max_points ON driver_max_points.driver_id = drivers.driver_id
  INNER JOIN races_ext AS races ON races.race_id = driver_standings.race_id

  LEFT JOIN (
    SELECT DISTINCT
      driver_standings.driver_id,
      COALESCE(MIN(beatable_drivers_next_race.current_position), driver_standings.position) AS best_position_next_race,
      COALESCE(MIN(beatable_drivers_this_season.current_position), driver_standings.position) AS best_position_this_season
    FROM driver_standings_ext AS driver_standings
      LEFT JOIN driver_max_points ON driver_max_points.driver_id = driver_standings.driver_id
      LEFT JOIN driver_max_points AS beatable_drivers_next_race ON beatable_drivers_next_race.current_points <= driver_max_points.max_points_next_race
      LEFT JOIN driver_max_points AS beatable_drivers_this_season ON beatable_drivers_this_season.current_points <= driver_max_points.max_points_this_season
    WHERE driver_standings.race_id = $race_id
    GROUP BY driver_standings.driver_id
  ) AS best_positions ON best_positions.driver_id = driver_standings.driver_id

  LEFT JOIN (
    SELECT DISTINCT
      driver_standings.driver_id,
      MIN(
        driver_standings.position + COALESCE(COUNT(DISTINCT threatening_drivers_next_race.driver_id), 0),
        COUNT(DISTINCT all_drivers.driver_id)
      ) AS worst_position_next_race,
      MIN(
        driver_standings.position + COALESCE(COUNT(DISTINCT threatening_drivers_this_season.driver_id), 0),
        COUNT(DISTINCT all_drivers.driver_id)
      ) AS worst_position_this_season
    FROM driver_standings_ext AS driver_standings
      LEFT JOIN driver_standings_ext AS all_drivers ON all_drivers.race_id = driver_standings.race_id
      LEFT JOIN driver_max_points ON driver_max_points.driver_id = driver_standings.driver_id
      LEFT JOIN driver_max_points AS threatening_drivers_next_race
        ON NOT(threatening_drivers_next_race.driver_id = driver_standings.driver_id)
        AND threatening_drivers_next_race.max_points_next_race >= driver_standings.points
      LEFT JOIN driver_max_points AS threatening_drivers_this_season
        ON NOT(threatening_drivers_this_season.driver_id = driver_standings.driver_id)
        AND threatening_drivers_this_season.max_points_this_season >= driver_standings.points
    WHERE driver_standings.race_id = $race_id
    GROUP BY driver_standings.driver_id
  ) AS worst_positions ON worst_positions.driver_id = driver_standings.driver_id

  LEFT JOIN drives
    ON drives.year = races.year
    AND drives.driver_id = drivers.driver_id
    AND drives.first_round <= races.round + 1
    AND (
      drives.is_final_drive_of_season
      OR drives.last_round >= races.round
    )

  LEFT JOIN constructors_ext AS constructors ON constructors.constructor_id = drives.constructor_id
  LEFT JOIN liveries
    ON liveries.constructor_ref = constructors.constructor_ref
    AND races.year BETWEEN liveries.start_year AND COALESCE(liveries.end_year, 9999)

WHERE
  driver_standings.race_id = $race_id

ORDER BY
  driver_standings.position ASC

;