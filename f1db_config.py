#! /usr/bin/env/python3
'''This file contains a variety of configuration parameters and hardcoded global constants.'''

DATABASE_FILE_NAME = "f1.db"

CSV_FILES_DIR = "./raw_data_files"
ERGAST_DOWNLOAD_URL = "http://ergast.com/downloads/f1db_csv.zip"
ERGAST_ZIP_FILE_NAME = "f1db.zip"

SQL_SCRIPT_FILES_DIR = "./sql_scripts"
TABLE_DEFINITION_SCRIPT_FILE = "define_base_tables.sql" # SQL script file that defines the DB tables
RELOAD_SCRIPT_FILES = [ # List of SQL script files that get run when the DB is reloaded from scratch
    "extended_base_tables.sql",
    "retirements.sql",
    "lap_positions.sql", # Depends on retirements
    "overtakes.sql" # Depends on lap_positions and retirements
]

CONSOLE_OUTPUT_ROW_LIMIT = 20 # Defines the maximum number of rows dumped out to the console