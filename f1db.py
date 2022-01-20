#! /usr/bin/env/python3
'''This program manages the process of setting up, connecting to, querying, and exporting from
a SQLite database of Formula 1 race data, which is provided by the Ergast API.
See http://ergast.com/mrd/ for more details about the API and the table structure.'''

import argparse, csv, logging, os, re, requests, sqlite3, zipfile
import pdb # pylint: disable = unused-import
import f1db_config as config # This file provides a lot of config parameters and global constants
import f1db_udfs # This file defines all user-defined functions to compile at connection setup

# Configure the logger so that we have a logger object to use.
logging.basicConfig(level = logging.NOTSET)
logger = logging.getLogger("f1db")

class Connection:
    '''This class wraps the sqlite3 Connection object to streamline the setup
    and teardown of connections. UDFs are compiled as part of the connection creation,
    and the connection can now be used via with/as instead of needing to close it manually.'''
    def __init__(self):
        self.connection = sqlite3.connect(config.DATABASE_FILE_NAME)
        self.connection.row_factory = sqlite3.Row
        self.compile_udfs()

        # "Aliasing" some functions of the underlying sqlite3.Connection object
        # so that they're callable directly without having to unwrap it.
        self.execute = self.connection.execute
        self.executemany = self.connection.executemany

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        '''This automatically closes the connection once the with/as is released.'''
        self.connection.close()

    def compile_udfs(self):
        '''This retrieves the list of user-defined functions from f1db_udfs and compiles each of them
        for use with the current connection. See f1db_udfs for more information about available UDFs.'''
        logger.debug("Compiling user-defined functions...")
        for udf_dict in f1db_udfs.USER_DEFINED_FUNCTIONS:
            if udf_dict["udf_type"] == "Scalar":
                compilation_function = self.connection.create_function
            else:
                compilation_function = self.connection.create_aggregate

            compilation_function(udf_dict["udf_name"], udf_dict["num_arguments"], udf_dict["udf_object"])

        logger.debug("UDF compilation complete.")

    def execute_sql_script_file(self, file_name):
        '''This opens and executes a SQL script file via the database connection.'''
        with open(os.path.join(config.SQL_SCRIPT_FILES_DIR, file_name), "r") as sql_script:
            self.connection.executescript(sql_script.read())

    def print_select_results(self, select_statement):
        '''This executes the provided SELECT statement and dumps out its output to the console.'''
        cursor = self.connection.execute(select_statement)
        print([x[0] for x in cursor.description])
        for row in cursor.fetchall()[:config.CONSOLE_OUTPUT_ROW_LIMIT]:
            print(list(row))

    def export_table_to_csv(self, table_name, output_file_name = None):
        '''This exports all records of a given table in the database to a CSV file.
        By default, the file name is the table's name plus ".csv", but a custom
        output file name can be provided.'''
        cursor = self.connection.execute("SELECT * FROM " + table_name)
        file_name = output_file_name if output_file_name else table_name + ".csv"
        with open(file_name, "w") as outfile:
            writer = csv.writer(outfile)
            writer.writerow([x[0] for x in cursor.description])
            writer.writerows([list(row) for row in cursor.fetchall()])

class Query:
    '''A Query represents

    A Query's data might be able to be visualized in more than one way, so a Query has a list
    of QueryVisualizations, which interact with the Plotly module to draw various kinds of charts.

    Queries, and their Visualizations ("QVizes"), are designed to be AS LAZY AS POSSIBLE!!
    - Queries are NOT run at compile time; we wait until they're actually requested.
    - The results of a query are NOT stored in memory; instead, we generate a new cursor when requested.
    - QVizes do not compile into a Figure object when they are loaded

    We do all of these things because the program is interactive, and might stay open for a long time.
    We want to make sure that the program does not hold onto any memory for any longer than it needs to,
    so Queries and QVizes prefer to recalculate things as needed (which in practice is relatively rare),
    and cache as little information as possible in the meantime.''' # Todo - finish this docstring

    def __init__(self, name, connection, output_table_name, sql_script_file_name):
        self.name = name
        self.connection = connection
        self.output_table_name = output_table_name
        self.sql_script_file_name = sql_script_file_name
        self.visualizations = []

        # Every time the program starts up, mark all queries as "not calculated yet."
        # The first time each query is executed, this flips to True and stays that
        # way until the program is closed. This lets us execute the query only once.
        self.has_been_calculated = False

    def calculate_results_table(self):
        '''This executes the SQL script responsible for calculating the query's output table.
        The table may already have existed in the database, but we don't know if it's up to date,
        so we run its code again to be sure. After we run its code for the first time, we assume
        that it's up to date for the rest of the lifetime of this program run,
        so we flip its flag to True and don't run it again until the program is restarted.'''
        self.connection.execute_sql_script_file(self.sql_script_file_name)
        self.has_been_calculated = True

    def get_results_records(self):
        '''This returns all of the records in the Query's output table.
        The output table is calculated first, if the Query hasn't been calculated yet.'''
        if not self.has_been_calculated:
            self.calculate_results_table()
        cursor = self.connection.execute("SELECT * FROM " + self.output_table_name)
        return [(x[0] for x in cursor.description)] + cursor.fetchall()

class QueryVisualization:
    '''A QueryVisualization''' # Todo - finish this docstring

    def __init__(self, query, figure_yaml):
        '''All that we store about a QVis when it gets created is the raw dictionary
        from the YAML structure. We do NOT compile that into a Figure yet! That happens
        later, on demand, when generate_figure is called. See QViz.generate_figure() for why.'''
        self.query = query
        self.figure_yaml = figure_yaml
        self.title = figure_yaml["title"]

    def generate_figure(self):
        '''This RETURNS a Figure - it does NOT set a class attribute!!

        Because we want this to be as lazy as possible, we rebuild the Figure FROM SCRATCH, each time we want it.
        This is tolerable because if we didn't do that, then the query results data would get stored in memory,
        because you can't compile a Figure without providing its data.

        To get around this, we don't generate the data, or the Figure, until we actually need it.
        This allows the Figure (and the data) to be garbage-collected as soon as we're done with the Figure.'''

        constructor = config.PLOTLY_FIGURE_TYPE_DICT[self.figure_yaml["figure_type"]]
        figure = constructor(
            self.query.get_results_records()
        )

    def export_png(self):
        '''This exports the QViz as a .png image.'''
        self.generate_figure().write_image(self.title.replace(" ", "_").lower() + ".png")

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

def redownload_files():
    '''This handles the process of redownloading the CSV files from the Ergast website.'''
    # Clear out all of the existing CSV files.
    logger.debug("Clearing out " + config.CSV_FILES_DIR + "...")
    for file_name in os.listdir(config.CSV_FILES_DIR):
        if file_name.endswith(".csv"):
            os.remove(os.path.join(config.CSV_FILES_DIR, file_name))
    logger.debug("Files removed.")

    logger.info("Downloading CSV zip file from Ergast...")
    with open(os.path.join(config.CSV_FILES_DIR, config.ERGAST_ZIP_FILE_NAME), "wb") as downfile:
        for data in requests.get(config.ERGAST_DOWNLOAD_URL, stream = True).iter_content():
            downfile.write(data)
    logger.info("Download complete.")

    # Extract the zip file we downloaded to the CSV file directory.
    logger.info("Extracting CSV files...")
    with zipfile.ZipFile(os.path.join(config.CSV_FILES_DIR, config.ERGAST_ZIP_FILE_NAME), "r") as csv_zip:
        csv_zip.extractall(config.CSV_FILES_DIR)
    logger.info("Extraction complete.")

    # Remove the downloaded zip file.
    logger.debug("Removing the downloaded zip file...")
    os.remove(os.path.join(config.CSV_FILES_DIR, config.ERGAST_ZIP_FILE_NAME))
    logger.debug("Zip file removed.")

def reload_database():
    '''This function reloads the SQLite database from scratch. The database file is deleted,
    then it is rebuilt by running TABLE_DEFINITION_SCRIPT_FILE to define the base tables,
    then populate_base_tables() to populate them. Finally, RELOAD_SCRIPT_FILES is run,
    which defines and calculates a number of supplemental tables.

    In practice, this function gets called when the --reload argument is provided on the command line.

    Yes, we could theoretically return the connection instead of spinning up a new one,
    but connections are cheap, and this helps keep the functions to a single responsibility.'''

    def populate_base_tables(connection):
        '''This function populates the base tables of the database from the CSV files
        downloaded from the Ergast API website. This must not be run until after the
        base tables have been defined, via the TABLE_DEFINITION_SCRIPT_FILE.'''
        for file_name in os.listdir(config.CSV_FILES_DIR):
            with open(os.path.join(config.CSV_FILES_DIR, file_name), "r") as infile:
                reader = csv.DictReader(infile)
                records = [[record[field_name] for field_name in reader.fieldnames] for record in reader]

            table_name = file_name.replace(".csv", "")
            field_names_tuple = re.sub(r'([a-z])([A-Z])', r'\1_\2', str(tuple(reader.fieldnames)).replace("'", "")).lower()
            question_marks_tuple = str(tuple(["?"] * len(reader.fieldnames))).replace("'", "")

            insert_statement = " ".join(["INSERT INTO", table_name, field_names_tuple, "VALUES", question_marks_tuple]) + ";"
            connection.connection.executemany(insert_statement, records)
            connection.connection.commit()

    os.remove(config.DATABASE_FILE_NAME) # Delete the SQLite database entirely
    with Connection() as connection:
        logger.debug("Defining base tables...")
        connection.execute_sql_script_file(config.TABLE_DEFINITION_SCRIPT_FILE)
        logger.debug("Base tables defined.")

        logger.info("Populating base tables...")
        populate_base_tables(connection)
        logger.info("Base tables populated.")

        for script_file in config.RELOAD_SCRIPT_FILES:
            logger.info("Running " + script_file + "...")
            connection.execute_sql_script_file(script_file)
            logger.info(script_file + " run successfully.")

def main():
    '''Execute top-level functionality.'''
    args = get_arguments()
    handle_arguments(args)

    with Connection() as conn:
        conn.execute_sql_script_file("display_tables.sql")
        pdb.set_trace()
        pass # pylint: disable = unnecessary-pass

main()