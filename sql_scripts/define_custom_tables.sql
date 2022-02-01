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
  "hex_code" VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY ("constructor_ref", "start_year", "end_year")
);