DROP TABLE IF EXISTS driver_standings_pretty;
CREATE TEMP TABLE driver_standings_pretty AS
SELECT DISTINCT
  races.year,
  races.round,
  races.short_name AS race_name,
  drivers.driver_id,
  drivers.full_name,
  drivers.surname,
  drivers.code,
  COALESCE(drives.drive_id, 0) AS drive_id,
  drives.is_first_drive_of_season AS is_first_drive,
  drives.is_final_drive_of_season AS is_final_drive,
  COALESCE(constructors.constructor_id, 0) AS constructor_id,
  COALESCE(constructors.short_name, "Hiatus") AS constructor_name,
  COALESCE(liveries.primary_hex_code, "#000000") AS hex_code,
  COALESCE(team_driver_ranks.team_driver_rank, 0) AS team_driver_rank,
  driver_standings.points,
  driver_standings.position,
  RANK() OVER legend_rank AS legend_rank

FROM drivers_ext AS drivers
  INNER JOIN driver_standings_ext AS driver_standings ON driver_standings.driver_id = drivers.driver_id
  INNER JOIN races_ext AS races ON races.race_id = driver_standings.race_id
  LEFT JOIN short_grand_prix_names ON short_grand_prix_names.full_name = races.name

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
  LEFT JOIN team_driver_ranks
    ON team_driver_ranks.year = races.year
    AND team_driver_ranks.constructor_id = constructors.constructor_id
    AND team_driver_ranks.driver_id = drivers.driver_id

WHERE races.year = 2005

WINDOW
  legend_rank AS (
    PARTITION BY
      races.year
    ORDER BY
      liveries.primary_hex_code,
      team_driver_ranks.team_driver_rank
  )

ORDER BY
  races.round,
  drivers.surname
;