CREATE TABLE "circuits" (
  "circuit_id" INT(11) NOT NULL,
  "circuit_ref" VARCHAR(255) NOT NULL DEFAULT '',
  "name" VARCHAR(255) NOT NULL DEFAULT '',
  "location" VARCHAR(255) DEFAULT NULL,
  "country" VARCHAR(255) DEFAULT NULL,
  "lat" FLOAT DEFAULT NULL,
  "lng" FLOAT DEFAULT NULL,
  "alt" INT(11) DEFAULT NULL,
  "url" VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY ("circuit_id")
);

CREATE TABLE "constructor_results" (
  "constructor_results_id" INT(11) NOT NULL,
  "race_id" INT(11) NOT NULL DEFAULT '0',
  "constructor_id" INT(11) NOT NULL DEFAULT '0',
  "points" FLOAT DEFAULT NULL,
  "status" VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY ("constructor_results_id")
);

CREATE TABLE "constructor_standings" (
  "constructor_standings_id" INT(11) NOT NULL,
  "race_id" INT(11) NOT NULL DEFAULT '0',
  "constructor_id" INT(11) NOT NULL DEFAULT '0',
  "points" FLOAT NOT NULL DEFAULT '0',
  "position" INT(11) DEFAULT NULL,
  "position_text" VARCHAR(255) DEFAULT NULL,
  "wins" INT(11) NOT NULL DEFAULT '0',
  PRIMARY KEY ("constructor_standings_id")
);

CREATE TABLE "constructors" (
  "constructor_id" INT(11) NOT NULL,
  "constructor_ref" VARCHAR(255) NOT NULL DEFAULT '',
  "name" VARCHAR(255) NOT NULL DEFAULT '',
  "nationality" VARCHAR(255) DEFAULT NULL,
  "url" VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY ("constructor_id")
);

CREATE TABLE "driver_standings" (
  "driver_standings_id" INT(11) NOT NULL,
  "race_id" INT(11) NOT NULL DEFAULT '0',
  "driver_id" INT(11) NOT NULL DEFAULT '0',
  "points" FLOAT NOT NULL DEFAULT '0',
  "position" INT(11) DEFAULT NULL,
  "position_text" VARCHAR(255) DEFAULT NULL,
  "wins" INT(11) NOT NULL DEFAULT '0',
  PRIMARY KEY ("driver_standings_id")
);

CREATE TABLE "drivers" (
  "driver_id" INT(11) NOT NULL,
  "driver_ref" VARCHAR(255) NOT NULL DEFAULT '',
  "number" INT(11) DEFAULT NULL,
  "code" VARCHAR(3) DEFAULT NULL,
  "forename" VARCHAR(255) NOT NULL DEFAULT '',
  "surname" VARCHAR(255) NOT NULL DEFAULT '',
  "full_name" VARCHAR(255) AS (forename || ' ' || surname) VIRTUAL,
  "dob" DATE DEFAULT NULL,
  "nationality" VARCHAR(255) DEFAULT NULL,
  "url" VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY ("driver_id")
);

CREATE TABLE "lap_times" (
  "race_id" INT(11) NOT NULL,
  "driver_id" INT(11) NOT NULL,
  "lap" INT(11) NOT NULL,
  "position" INT(11) DEFAULT NULL,
  "time" VARCHAR(255) DEFAULT NULL,
  "milliseconds" INT(11) DEFAULT NULL,
  "seconds" FLOAT AS (CAST(milliseconds AS FLOAT) / 1000) VIRTUAL,
  PRIMARY KEY ("race_id", "driver_id", "lap")
);

CREATE TABLE "pit_stops" (
  "race_id" INT(11) NOT NULL,
  "driver_id" INT(11) NOT NULL,
  "stop" INT(11) NOT NULL,
  "lap" INT(11) NOT NULL,
  "time" TIME NOT NULL,
  "duration" VARCHAR(255) DEFAULT NULL,
  "milliseconds" INT(11) DEFAULT NULL,
  "seconds" FLOAT AS (CAST(milliseconds AS FLOAT) / 1000) VIRTUAL,
  PRIMARY KEY ("race_id", "driver_id", "stop")
);

CREATE TABLE "qualifying" (
  "qualify_id" INT(11) NOT NULL,
  "race_id" INT(11) NOT NULL DEFAULT '0',
  "driver_id" INT(11) NOT NULL DEFAULT '0',
  "constructor_id" INT(11) NOT NULL DEFAULT '0',
  "number" INT(11) NOT NULL DEFAULT '0',
  "position" INT(11) DEFAULT NULL,
  "q1" VARCHAR(255) DEFAULT NULL,
  "q2" VARCHAR(255) DEFAULT NULL,
  "q3" VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY ("qualify_id")
);

CREATE TABLE "races" (
  "race_id" INT(11) NOT NULL,
  "year" INT(11) NOT NULL DEFAULT '0',
  "round" INT(11) NOT NULL DEFAULT '0',
  "circuit_id" INT(11) NOT NULL DEFAULT '0',
  "name" VARCHAR(255) NOT NULL DEFAULT '',
  "date" DATE NOT NULL,
  "time" TIME DEFAULT NULL,
  "url" VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY ("race_id")
);

CREATE TABLE "results" (
  "result_id" INT(11) NOT NULL,
  "race_id" INT(11) NOT NULL DEFAULT '0',
  "driver_id" INT(11) NOT NULL DEFAULT '0',
  "constructor_id" INT(11) NOT NULL DEFAULT '0',
  "number" INT(11) DEFAULT NULL,
  "grid" INT(11) NOT NULL DEFAULT '0',
  "position" INT(11) DEFAULT NULL,
  "position_text" VARCHAR(255) NOT NULL DEFAULT '',
  "position_order" INT(11) NOT NULL DEFAULT '0',
  "points" FLOAT NOT NULL DEFAULT '0',
  "laps" INT(11) NOT NULL DEFAULT '0',
  "time" VARCHAR(255) DEFAULT NULL,
  "milliseconds" INT(11) DEFAULT NULL,
  "fastest_lap" INT(11) DEFAULT NULL,
  "rank" INT(11) DEFAULT '0',
  "fastest_lap_time" VARCHAR(255) DEFAULT NULL,
  "fastest_lap_speed" VARCHAR(255) DEFAULT NULL,
  "status_id" INT(11) NOT NULL DEFAULT '0',
  PRIMARY KEY ("result_id")
);

CREATE TABLE "seasons" (
  "year" INT(11) NOT NULL DEFAULT '0',
  "url" VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY ("year")
);

CREATE TABLE "status" (
  "status_id" INT(11) NOT NULL,
  "status" VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY ("status_id")
);

CREATE TABLE "sprint_results" (
  "result_id" INT(11) NOT NULL,
  "race_id" INT(11) NOT NULL DEFAULT '0',
  "driver_id" INT(11) NOT NULL DEFAULT '0',
  "constructor_id" INT(11) NOT NULL DEFAULT '0',
  "number" INT(11) DEFAULT NULL,
  "grid" INT(11) NOT NULL DEFAULT '0',
  "position" INT(11) DEFAULT NULL,
  "position_text" VARCHAR(255) NOT NULL DEFAULT '',
  "position_order" INT(11) NOT NULL DEFAULT '0',
  "points" FLOAT NOT NULL DEFAULT '0',
  "laps" INT(11) NOT NULL DEFAULT '0',
  "time" VARCHAR(255) DEFAULT NULL,
  "milliseconds" INT(11) DEFAULT NULL,
  "fastest_lap" INT(11) DEFAULT NULL,
  "fastest_lap_time" VARCHAR(255) DEFAULT NULL,
  "fastest_lap_speed" VARCHAR(255) DEFAULT NULL,
  "status_id" INT(11) NOT NULL DEFAULT '0',
  PRIMARY KEY ("result_id")
);
