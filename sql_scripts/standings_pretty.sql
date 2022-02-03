

DROP TABLE IF EXISTS driver_standings_pretty;
CREATE TEMP TABLE driver_standings_pretty AS
SELECT DISTINCT
  races.year,
  races.round,
  COALESCE(short_grand_prix_names.short_name, races.name) AS race_name,
  drivers.driver_id,
  drivers.full_name,
  drivers.surname,
  drivers.code,
  COALESCE(constructors.constructor_id, LAG(constructors.constructor_id) OVER previous_race) AS constructor_id,
  COALESCE(
    short_constructor_names.short_name,
    constructors.name,
    LAG(COALESCE(short_constructor_names.short_name, constructors.name)) OVER previous_race
  ) AS constructor_name,
  COALESCE(liveries.primary_hex_code, LAG(liveries.primary_hex_code) OVER previous_race, "#000000") AS hex_code,
  COALESCE(team_driver_ranks.team_driver_rank, LAG(team_driver_ranks.team_driver_rank) OVER previous_race) AS team_driver_rank,
  driver_standings.points,
  driver_standings.position

FROM drivers
  INNER JOIN driver_standings ON driver_standings.driver_id = drivers.driver_id
  INNER JOIN races ON races.race_id = driver_standings.race_id
  LEFT JOIN short_grand_prix_names ON short_grand_prix_names.full_name = races.name
  LEFT JOIN results
    ON results.race_id = races.race_id
    AND results.driver_id = drivers.driver_id
  LEFT JOIN constructors ON constructors.constructor_id = results.constructor_id
  LEFT JOIN short_constructor_names ON short_constructor_names.constructor_ref = constructors.constructor_ref
  LEFT JOIN liveries
    ON liveries.constructor_ref = constructors.constructor_ref
    AND races.year BETWEEN liveries.start_year AND COALESCE(liveries.end_year, 9999)
  LEFT JOIN team_driver_ranks
    ON team_driver_ranks.year = races.year
    AND team_driver_ranks.constructor_id = constructors.constructor_id
    AND team_driver_ranks.driver_id = drivers.driver_id

  INNER JOIN (
    SELECT
      races.year,
      results.driver_id,
      results.constructor_id,
      MIN(races.round) AS first_round,
      MAX(races.round) AS last_round
    FROM results
      INNER JOIN races ON races.race_id = results.race_id
    GROUP BY
      races.year,
      results.driver_id,
      results.constructor_id
  ) AS

WHERE
  races.year = 2017

WINDOW
  previous_race AS (
    PARTITION BY drivers.driver_id
    ORDER BY races.round ASC
  )

ORDER BY
  races.round,
  drivers.surname
;