#! /usr/bin/env/python3
'''This program manages the process of setting up, connecting to, querying, and exporting from
a SQLite database of Formula 1 race data, which is provided by the Ergast API.
See http://ergast.com/mrd/ for more details about the API and the table structure.'''

import argparse, csv, logging, os, re, requests, sqlite3, zipfile
import pdb # pylint: disable = unused-import
import f1db_udfs # This file defines all user-defined functions to compile at connection setup

# Configure the logger so that we have a logger object to use.
logging.basicConfig(level = logging.NOTSET)
logger = logging.getLogger("f1db")

DATABASE_FILE_NAME = "f1.db"

SQL_SCRIPT_FILES_DIR = "./sql_scripts"
TABLE_DEFINITION_SCRIPT_FILE = "define_base_tables.sql"
RELOAD_SCRIPT_FILES = [
    "extended_base_tables.sql",
    "retirements.sql",
    "lap_positions.sql", # Depends on retirements
    "overtakes.sql" # Depends on lap_positions and retirements
]

CSV_FILES_DIR = "./raw_data_files"
ERGAST_DOWNLOAD_URL = "http://ergast.com/downloads/f1db_csv.zip"
ERGAST_ZIP_FILE_NAME = "f1db.zip"

CONSOLE_OUTPUT_ROW_LIMIT = 20 # Defines the maximum number of rows dumped out to the console

def get_arguments():
    '''This handles the parsing of various arguments to the script.'''
    parser = argparse.ArgumentParser(description = "Connect to the F1 SQLite database (or reload it from the CSV files) and run queries against it.")
    parser.add_argument("-r", "--reload", action = "store_true")
    parser.add_argument("-d", "--download", action = "store_true")
    parser.add_argument("-q", "--quiet", action = "store_true")
    parser.add_argument("-v", "--verbose", action = "store_true")
    return parser.parse_args()

def handle_arguments(arguments):
    '''This executes some one-off functionality based on specific argument values.'''
    if arguments.verbose:
        logger.setLevel(logging.DEBUG)
    elif arguments.quiet:
        logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.INFO)

    if arguments.download:
        logger.debug("Download option provided, redownloading files")
        redownload_files()

    # We want to reload the DB if the files were re-downloaded, even if not explicitly specified.
    if arguments.reload or arguments.download:
        logger.debug("Download or reload arguments provided, reloading database")
        reload_database()

def compile_udfs(connection):
    '''This retrieves the list of user-defined functions from f1db_udfs and compiles each of them
    for use with the current connection. See f1db_udfs for more information about available UDFs.'''
    logger.debug("Compiling user-defined functions...")
    for udf_dict in f1db_udfs.USER_DEFINED_FUNCTIONS:
        compilation_function = connection.create_function if udf_dict["udf_type"] == "Scalar" else connection.create_aggregate
        compilation_function(udf_dict["udf_name"], udf_dict["num_arguments"], udf_dict["udf_object"])
    logger.debug("UDF compilation complete.")

def populate_base_tables(connection):
    '''This function populates the base tables of the database from the CSV files
    downloaded from the Ergast API website. This must not be run until after the
    base tables have been defined, via TABLE_DEFINITION_SCRIPT_FILE.'''
    for file_name in os.listdir(CSV_FILES_DIR):
        with open(os.path.join(CSV_FILES_DIR, file_name), "r") as infile:
            reader = csv.DictReader(infile)
            records = [[record[field_name] for field_name in reader.fieldnames] for record in reader]

        table_name = file_name.replace(".csv", "")
        field_names_tuple = re.sub(r'([a-z])([A-Z])', r'\1_\2', str(tuple(reader.fieldnames)).replace("'", "")).lower()
        question_marks_tuple = str(tuple(["?"] * len(reader.fieldnames))).replace("'", "")

        insert_statement = " ".join(["INSERT INTO", table_name, field_names_tuple, "VALUES", question_marks_tuple]) + ";"
        connection.executemany(insert_statement, records)
        connection.commit()

def redownload_files():
    '''This handles the process of redownloading the CSV files from the Ergast website.'''
    # Clear out all of the existing CSV files.
    logger.debug("Clearing out " + CSV_FILES_DIR + "...")
    for file_name in os.listdir(CSV_FILES_DIR):
        if file_name.endswith(".csv"):
            os.remove(os.path.join(CSV_FILES_DIR, file_name))
    logger.debug("Files removed.")

    logger.info("Downloading CSV zip file from Ergast...")
    with open(os.path.join(CSV_FILES_DIR, ERGAST_ZIP_FILE_NAME), "wb") as downfile:
        for data in requests.get(ERGAST_DOWNLOAD_URL, stream = True).iter_content():
            downfile.write(data)
    logger.info("Download complete.")

    # Extract the zip file we downloaded to the CSV file directory.
    logger.info("Extracting CSV files...")
    with zipfile.ZipFile(os.path.join(CSV_FILES_DIR, ERGAST_ZIP_FILE_NAME), "r") as csv_zip:
        csv_zip.extractall(CSV_FILES_DIR)
    logger.info("Extraction complete.")

    # Remove the downloaded zip file.
    logger.debug("Removing the downloaded zip file...")
    os.remove(os.path.join(CSV_FILES_DIR, ERGAST_ZIP_FILE_NAME))
    logger.debug("Zip file removed.")

def reload_database():
    '''This function reloads the SQLite database from scratch. The database file is deleted,
    then it is rebuilt by running TABLE_DEFINITION_SCRIPT_FILE to define the base tables,
    then populate_base_tables() to populate them. Finally, RELOAD_SCRIPT_FILES is run,
    which defines and calculates a number of supplemental tables.

    In practice, this function gets called when the --reload argument is provided on the command line.

    Yes, we could theoretically return the connection instead of spinning up a new one,
    but connections are cheap, and this helps keep the functions to a single responsibility.'''
    os.remove(DATABASE_FILE_NAME) # Delete the SQLite database entirely
    connection = initialize_connection()

    logger.debug("Defining base tables...")
    execute_sql_script_file(connection, TABLE_DEFINITION_SCRIPT_FILE)
    logger.debug("Base tables defined.")

    logger.info("Populating base tables...")
    populate_base_tables(connection)
    logger.info("Base tables populated.")

    for script_file in RELOAD_SCRIPT_FILES:
        logger.info("Running " + script_file + "...")
        execute_sql_script_file(connection, script_file)
        logger.info(script_file + " run successfully.")

def initialize_connection():
    '''This handles the setup of a connection to the database, and executes some setup tasks
    that need to be run for each new connection (notably, the compilation of UDFs).'''
    connection = sqlite3.connect(DATABASE_FILE_NAME)
    connection.row_factory = sqlite3.Row
    compile_udfs(connection)
    return connection

def execute_sql_script_file(connection, file_name):
    '''This executes one or more SQL script files via the provided connection.
    The file_names argument can be a single file name or a list of file names.'''
    with open(os.path.join(SQL_SCRIPT_FILES_DIR, file_name), "r") as sql_script:
        connection.executescript(sql_script.read())

def print_select_results(connection, select_statement):
    '''This executes a SELECT statement as text and dumps out its output to the console.'''
    for row in connection.execute(select_statement).fetchall()[:CONSOLE_OUTPUT_ROW_LIMIT]:
        print(tuple(row))

def export_table_to_csv(connection, table_name, output_file_name = None):
    '''This exports all records of a given table in the database to a CSV file.
    By default, the file name is the table's name plus ".csv", but a custom
    output file name can be provided, if so desired.'''
    cursor = connection.execute("SELECT * FROM " + table_name)
    file_name = output_file_name if output_file_name else table_name + ".csv"
    with open(file_name, "w") as outfile:
        writer = csv.writer(outfile)
        writer.writerow([x[0] for x in cursor.description])
        writer.writerows([list(row) for row in cursor.fetchall()])

# These definitions basically "alias" these functions so they're easier to type in the CLI
xptt = export_table_to_csv
essf = execute_sql_script_file
psr = print_select_results

def main():
    '''Execute top-level functionality.'''
    args = get_arguments()
    handle_arguments(args)

    c = initialize_connection()
    execute_sql_script_file(c, "display_tables.sql")

    pdb.set_trace()

    c.close()

main()