DROP TABLE IF EXISTS overtakes_by_race;
CREATE TEMP TABLE overtakes_by_race AS
SELECT DISTINCT
  races.round,
  races.name AS race_name,
  COALESCE(COUNT(overtakes.race_id), 0) AS num_overtakes

FROM races
  LEFT JOIN overtakes
    ON overtakes.race_id = races.race_id
    AND overtakes.overtake_type == "T"

WHERE
  races.year == 2022

GROUP BY
  races.race_id

ORDER BY
  num_overtakes DESC

;
