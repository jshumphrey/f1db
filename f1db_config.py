#! /usr/bin/env/python3
'''This file contains a variety of configuration parameters and hardcoded global constants.'''
import plotly.io, plotly.express

DATABASE_FILE_NAME = "f1.db"

BASE_CSV_FILES_DIR = "./raw_data_files"
CUSTOM_CSV_FILES_DIR = "./custom_data_files"
ERGAST_DOWNLOAD_URL = "http://ergast.com/downloads/f1db_csv.zip"
ERGAST_ZIP_FILE_NAME = "f1db.zip"

SQL_SCRIPT_FILES_DIR = "./sql_scripts"
BASE_TABLE_DEFINITION_SCRIPT_FILE = "define_base_tables.sql" # SQL script file that defines the DB tables
CUSTOM_TABLE_DEFINITION_SCRIPT_FILE = "define_custom_tables.sql" # SQL script file that defines the DB tables
RELOAD_SCRIPT_FILES = [ # List of SQL script files that get run when the DB is reloaded from scratch
    "extended_base_tables.sql",
	"team_driver_ranks.sql",
	"drives.sql",
    "retirements.sql",
    "lap_positions.sql", # Depends on retirements
    "overtakes.sql" # Depends on lap_positions and retirements
]

CONSOLE_OUTPUT_ROW_LIMIT = 20 # Defines the maximum number of rows dumped out to the console

QUERY_YAML_FILE_NAME = "f1db_queries.yml"
QVIZ_YAML_IGNORED_ATTRIBUTES = ["figure_type"]
QVIS_YAML_ATTR_TRANSLATIONS = {
	"x_column_name": "x",
	"y_column_name": "y",
	"color_column_name": "color",
	"value_to_color_dict": "color_discrete_map"
}

PLOTLY_FIGURE_TYPE_DICT = { # This translates a figure-type string into the actual Plotly constructor function.
	"Line": plotly.express.line,
	"Bar": plotly.express.bar,
	"Histogram": plotly.express.histogram,
	"Scatter": plotly.express.scatter,
	"Box": plotly.express.box
}