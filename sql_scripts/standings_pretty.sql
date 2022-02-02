DROP TABLE IF EXISTS driver_standings_pretty;
CREATE TEMP TABLE driver_standings_pretty AS
SELECT DISTINCT
  drivers.full_name,
  drivers.surname,
  drivers.code,
  COALESCE(liveries.primary_hex_code, "#000000") AS primary_hex_code,
  races.round,
  races.name,
  COALESCE(short_grand_prix_names.short_name, races.name) AS short_name,
  driver_standings.points,
  driver_standings.position AS rank

FROM drivers
  INNER JOIN driver_standings ON driver_standings.driver_id = drivers.driver_id
  INNER JOIN races ON races.race_id = driver_standings.race_id
  LEFT JOIN short_grand_prix_names ON short_grand_prix_names.full_name = races.name
  INNER JOIN results
    ON results.race_id = races.race_id
    AND results.driver_id = drivers.driver_id
  INNER JOIN constructors ON constructors.constructor_id = results.constructor_id
  LEFT JOIN liveries
    ON liveries.constructor_ref = constructors.constructor_ref
    AND races.year BETWEEN liveries.start_year AND COALESCE(liveries.end_year, 9999)

WHERE
  races.year = 2021

ORDER BY
  races.round,
  drivers.surname
;

DROP TABLE IF EXISTS constructor_standings_pretty;
CREATE TEMP TABLE constructor_standings_pretty AS
SELECT DISTINCT
  constructors.name,
  races.round,
  races.name,
  COALESCE(short_grand_prix_names.short_name, races.name) AS short_name,
  constructor_standings.points,
  constructor_standings.position AS rank

FROM constructors
  INNER JOIN constructor_standings ON constructor_standings.constructor_id = constructors.constructor_id
  INNER JOIN races
    ON races.race_id = constructor_standings.race_id
    AND races.year = 2021
  LEFT JOIN short_grand_prix_names ON short_grand_prix_names.full_name = races.name

ORDER BY
  races.round,
  constructors.name
;