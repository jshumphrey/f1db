CREATE TABLE "short_grand_prix_names" (
  "full_name" VARCHAR(255) NOT NULL DEFAULT '',
  "short_name" VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY ("full_name")
);

CREATE TABLE "short_constructor_names" (
  "constructor_ref" VARCHAR(255) NOT NULL DEFAULT '',
  "short_name" VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY ("constructor_ref")
);

CREATE TABLE "liveries" (
  "constructor_ref" VARCHAR(255) NOT NULL DEFAULT '',
  "start_year" INT(11) NOT NULL DEFAULT '0',
  "end_year" INT(11) NULL DEFAULT '0',
  "primary_hex_code" VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY ("constructor_ref", "start_year", "end_year")
);

CREATE TABLE "tdr_overrides" (
  "year" INT(11) NOT NULL DEFAULT '0',
  "constructor_ref" VARCHAR(255) NOT NULL DEFAULT '',
  "driver_ref" VARCHAR(255) NOT NULL DEFAULT '',
  "team_driver_rank" INT(11) NULL DEFAULT '0',
  PRIMARY KEY ("year", "constructor_ref", "driver_ref")
);