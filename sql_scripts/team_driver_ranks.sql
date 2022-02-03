DROP TABLE IF EXISTS team_driver_ranks;
CREATE TABLE team_driver_ranks AS
SELECT DISTINCT
  races.year,
  constructors.constructor_id,
  constructors.constructor_ref,
  drivers.driver_id,
  drivers.driver_ref,
  COALESCE(tdr_overrides.team_driver_rank, DENSE_RANK() OVER single_season) AS team_driver_rank

FROM races
  INNER JOIN results ON results.race_id = races.race_id
  INNER JOIN drivers ON drivers.driver_id = results.driver_id
  INNER JOIN constructors ON constructors.constructor_id = results.constructor_id

  INNER JOIN (
    SELECT DISTINCT
      races.year,
      driver_standings.driver_id,
      driver_standings.points,
      driver_standings.position
    FROM driver_standings
      INNER JOIN races ON races.race_id = driver_standings.race_id
    GROUP BY
      races.year,
      driver_standings.driver_id
    HAVING races.round = MAX(races.round)
  ) AS eoy_standings
    ON eoy_standings.year = races.year
    AND eoy_standings.driver_id = drivers.driver_id

  LEFT JOIN tdr_overrides
    ON tdr_overrides.year = races.year
    AND tdr_overrides.constructor_ref = constructors.constructor_ref
    AND tdr_overrides.driver_ref = drivers.driver_ref

WINDOW
  single_season AS (
    PARTITION BY
      races.year,
      constructors.constructor_id
    ORDER BY
      eoy_standings.position ASC
  )

ORDER BY
  races.year,
  constructors.constructor_id,
  team_driver_rank ASC

;