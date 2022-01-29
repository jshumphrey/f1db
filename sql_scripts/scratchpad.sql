DROP TABLE IF EXISTS scratchpad;
CREATE TEMP TABLE scratchpad AS
SELECT DISTINCT
  drivers.surname,
  drivers.full_name,
  drivers.code

FROM drivers AS drivers
  INNER JOIN results ON results.driver_id = drivers.driver_id
  INNER JOIN races
    ON races.race_id = results.race_id
    AND races.year >= 1990

WHERE
  NOT (drivers.code = '\N')

ORDER BY
  drivers.surname ASC
;