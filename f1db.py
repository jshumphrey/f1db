#! /usr/bin/env/python3
'''This program manages the process of setting up, connecting to, querying, and exporting from
a SQLite database of Formula 1 race data, which is provided by the Ergast API.
See http://ergast.com/mrd/ for more details about the API and the table structure.'''

# Todo: Add some fancy exception handling to check to see whether
# the optional pip packages are installed. Also check for Kaleido!!!
# See https://stackoverflow.com/questions/301134/how-to-import-a-module-given-its-name-as-string

# Standard-library imports
import argparse, csv, logging, os, platform, re, sqlite3, sys, textwrap, zipfile

# Third-party imports
import pandas, requests, yaml

# Other Python modules that are part of this program
import f1db_config as config # This file provides a lot of config parameters and global constants
import f1db_udfs # This file defines all user-defined functions to compile at connection setup

# Configure the logger so that we have a logger object to use.
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger("f1db")

# Set up a global TextWrapper (seriously, do you really want to pass this around to everyone?)
# and configure it to wrap text nicely for all of the displayed console
wrapper = textwrap.TextWrapper()

class InputError(Exception):
    '''This is a custom exception raised when a user's input is unacceptable.'''
    pass # pylint: disable = unnecessary-pass

class Connection:
    '''This class wraps the sqlite3 Connection object to streamline the setup
    and teardown of connections. UDFs are compiled as part of the connection creation,
    and the connection can now be used via with/as instead of needing to close it manually.'''

    def __init__(self):
        self.connection = sqlite3.connect(config.DATABASE_FILE_NAME)
        self.connection.row_factory = sqlite3.Row
        self.compile_udfs()
        self.queries = [] # This is populated via bind_queries()

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

    def bind_queries(self, query_yaml_file_name):
        '''This populates self.queries with the contents of a YAML file of query definitions.'''
        with open(query_yaml_file_name, "r") as queries_yaml:
            logger.debug("Binding queries...")
            self.queries += [Query(self, query_yaml) for query_yaml in yaml.load_all(queries_yaml, Loader = yaml.SafeLoader)]
            logger.debug("Queries bound successfully.")

    def execute_sql_script_file(self, file_name, **kwargs):
        '''This opens and executes a SQL script file via the database connection.'''
        with open(os.path.join(config.SQL_SCRIPT_FILES_DIR, file_name), "r") as script_file:
            script_text = script_file.read()

        parameters = set(re.findall(r"(\$[a-zA-Z0-9_]+)", script_text))
        for parameter in parameters:
            if parameter.replace("$", "") not in kwargs:
                value = input(f"Please provide a value for '{parameter}' in {file_name}: ")
            else:
                value = str(kwargs[parameter.replace("$", "")])

            script_text = script_text.replace(parameter, value)

        self.connection.executescript(script_text)

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
        logger.debug(f"Acquiring cursor with which to export {table_name}...")
        cursor = self.connection.execute(f"SELECT * FROM {table_name}")
        logger.debug("Cursor acquired successfully.")

        file_name = output_file_name if output_file_name else table_name + ".csv"
        with open(file_name, "w") as outfile:
            logger.debug(f"Exporting {table_name} to {file_name}...")
            writer = csv.writer(outfile, quoting = csv.QUOTE_NONNUMERIC)
            writer.writerow([x[0] for x in cursor.description])
            writer.writerows([list(row) for row in cursor.fetchall()])
            logger.debug("Export complete.")

class Query:
    '''A Query represents a single piece of SQL code whose output is a single database table;
    typically a temporary table. It's fine if the SQL code generates multiple preliminary tables,
    but the final product should be a single output table, ready to be examined or visualized.

    This output table should be complete: in other words, all calculations should be done, all fields
    should be present and named appropriately, and all values should be suitable for display to the user.

    A Query's data might be able to be visualized in more than one way, so a Query has a list
    of QueryVisualizations. Each QueryVisualization ("QViz") contains information that is used by the
    "Plotly" Python module; the QViz tells Plotly how to use the Query's output table to draw
    a particular chart. Each QViz corresponds to a single chart specification.

    Queries, and their Visualizations, are designed to be AS LAZY AS POSSIBLE!!
    - Queries are NOT run when they are instantiated; we wait until they're actually requested.
    - The results of a query are NOT stored in memory; instead, we generate a new cursor when requested.
    - QVizes do not compile into a Plotly Figure object when they are instantiated; instead, we compile
      a new Figure object from scratch each time the QViz is actually drawn/exported.

    We do all of these things because the program is interactive, and might stay open for a long time.
    We want to make sure that the program does not hold onto any memory for any longer than it needs to,
    so Queries and QVizes prefer to recalculate things as needed (which in practice is relatively rare),
    and cache as little information as possible in the meantime.'''

    def __init__(self, connection, query_yaml):
        self.connection = connection
        self.name = query_yaml["name"]
        self.output_table_name = query_yaml["output_table_name"]
        self.sql_script_file_name = query_yaml["sql_script_file_name"]
        self.visualizations = [QueryVisualization(self, viz_yaml) for viz_yaml in query_yaml["visualizations"]]

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
        cursor = self.connection.execute(f"SELECT * FROM {self.output_table_name}")
        return [(x[0] for x in cursor.description)] + cursor.fetchall()

    def generate_results_dataframe(self):
        '''This returns a Pandas dataframe containing the records in the Query's output table.
        The output table is calculated first, if the Query hasn't been calculated yet.'''
        if not self.has_been_calculated:
            self.calculate_results_table()
        return pandas.read_sql_query(f"SELECT * FROM {self.output_table_name}", self.connection.connection)

    def export_table_to_csv(self):
        '''This function is a property of the query's connection, but defining it here
        exposes it at the Query level as well.'''
        self.connection.export_table_to_csv(self.output_table_name)

class QueryVisualization:
    '''A QueryVisualization provides input to Plotly on how to draw a single chart
    from the output table of its parent Query. See the Query docstring for more details.'''

    def __init__(self, query, viz_yaml):
        '''All that we store for a QVis when it gets created is the raw dictionary
        from the YAML structure. We do NOT compile that into a Figure yet! That happens
        later, on demand, when generate_figure is called. See QViz.generate_figure() for why.'''

        self.query = query
        self.viz_yaml = viz_yaml
        self.title = viz_yaml["title"]
        self.figure_type = viz_yaml["figure_type"]

    def generate_figure(self):
        '''This generates and RETURNS a Figure - it does NOT set a class attribute!!

        Because we want this to be as lazy as possible, we rebuild the Figure FROM SCRATCH, each time we want it.
        This is tolerable because if we didn't do that, then the Query's results data would get stored in memory,
        because you can't generating a Figure without providing its full input data records right then and there.

        To get around this, we don't generate the data, or the Figure, until we actually need it.
        This allows the Figure (and the data) to be garbage-collected as soon as we're done with the Figure.'''

        # Plotly uses different Figure sub-classes for different figure types, so
        # PLOTLY_FIGURE_TYPE_DICT translates the figure_type string in the viz_yaml
        # into the actual subclass constructor we need to call.
        constructor = config.PLOTLY_FIGURE_TYPE_DICT[self.viz_yaml["figure_type"]]

        # figure_attributes is a dictionary of parameters that will get passed to the
        # constructor to compile the figure. These parameters are loaded from the viz_yaml,
        # but because we want to use more-readable attribute names in viz_yaml, the
        # parameter names first get run through QVIS_YAML_ATTR_TRANSLATIONS.
        #
        # Additionally, some of the attributes in viz_yaml shouldn't be passed
        # to the constructor, so those are filtered out by QVIZ_YAML_IGNORED_ATTRIBUTES.
        figure_attributes = {
            config.QVIS_YAML_ATTR_TRANSLATIONS[key] if key in config.QVIS_YAML_ATTR_TRANSLATIONS else key: value
            for key, value in self.viz_yaml.items()
            if key not in config.QVIZ_YAML_IGNORED_ATTRIBUTES
        }

        return constructor(data_frame = self.query.generate_results_dataframe(), **figure_attributes)

    def export_png(self):
        '''This exports the QViz as a .png image.'''
        self.generate_figure().write_image(self.title.replace(" ", "_").lower() + ".png", engine = "kaleido")

class Menu:
    '''A Menu represents a single screen from which the user can select from a list of options.
    These options are represented as MenuItems in menu.menu_items.

    The main function that makes a Menu "do things" is menu.run(). Menus loop forever until
    something causes them to exit; this would normally be the user entering the "go back" menu option
    or the "exit the program" menu option, but could also be any kind of uncaught exception.
    If neither of these things happen, the default behavior is to re-display the current menu
    after the user's selection has been received and executed.

    Menus can have submenus underneath them; a submenu is also a Menu and has its own MenuItems.
    To have a MenuItem display a submenu, set its "function" argument to [submenu].run .
    '''
    def __init__(self, connection, parent_menu = None, text = None, allows_multi_select = False):
        self.connection = connection
        self.parent_menu = parent_menu
        self.text = text
        self.allows_multi_select = allows_multi_select

        self.menu_items = []
        self.default_menu_items = self.generate_default_menu_items()

    def generate_default_menu_items(self):
        '''This wraps the process of generating the default menu items for this menu.'''
        default_items = [MenuSeparator()]
        if self.parent_menu:
            default_items += [MenuItem(self, "Return to the previous menu.", lambda *args: None, exit_action = "BREAK")] # The lambda here acts as a no-op.
        default_items += [
            MenuItem(self, "Drop to the PDB debug console.", breakpoint),
            MenuItem(self, "Exit the program.", sys.exit, function_args = [0])
        ]

        return default_items

    def get_enumerated_items(self):
        '''This returns a dict of index: item for all DISPLAYED MenuItems for this Menu.
        "Displayed", here, means that enumerated_items DOES include the default menu items,
        but does NOT include menu separators; those do not receive an index since they're
        not selectable by the user.'''
        return {i: x for i, x in enumerate([x for x in self.menu_items + self.default_menu_items if not isinstance(x, MenuSeparator)], 1)}

    def get_user_selections(self):
        '''This wraps the process of requesting the input string of menu selections
        from the user, validating that input, and passing the input back to the main loop.'''
        print(wrapper.fill("Please make a selection from the menu by entering its item number."))

        if self.allows_multi_select:
            print(wrapper.fill("Multiple selections can be queued by entering multiple item numbers, separated by a space - for example, \"1 3 5\"."))
            user_input = input("Enter your selection(s): ")
        else:
            user_input = input("Enter your selection: ")

        self.validate_user_input(user_input)
        return user_input.split()

    def validate_user_input(self, user_input):
        '''This looks at input provided by the user at the selections menu and
        checks for various issues. InputError is raised if any issues are found.'''
        if not self.allows_multi_select and len(user_input.split()) > 1:
            raise InputError("This menu only allows you to select one item!")

        non_integer_inputs = [x for x in user_input.split() if not x.isdigit()]
        if non_integer_inputs:
            raise InputError("The following selections are not numbers: " + ", ".join(non_integer_inputs) + "!")

        out_of_bounds_inputs = [x for x in user_input.split() if int(x) not in self.get_enumerated_items()]
        if out_of_bounds_inputs:
            raise InputError("The following selections are not in this menu's selections: " + ", ".join(out_of_bounds_inputs) + "!")

    def draw(self):
        '''This wraps the process of drawing all of this menu's text and menu items.
        Note that the menu items here will include additional menu items from extended_menu_items,
        typically a "go back", an "exit" and a "drop to debug" option.'''
        # Clear the console, and print the menu's header.
        if platform.system().lower() == 'windows':
            os.system("cls")
        else:
            os.system("reset")
        print(wrapper.fill(self.text))
        print() # Prints a blank line.

        index = 1
        for menu_item in self.menu_items + self.default_menu_items:
            if isinstance(menu_item, MenuSeparator):
                print(wrapper.fill(menu_item.text))
            else:
                print(wrapper.fill(f"{index!s}. {menu_item.text}"))
                index += 1

        print() # Prints a blank line.

    def run(self):
        '''This is the main loop that actually displays the menu and handles the user's input.'''
        while True:
            self.draw() # Display all of this menu's text and menu items.

            # Take the user's input and handle their selections.
            try:
                selections = self.get_user_selections()
            except InputError as e: # If the user provides bad input, display its message and have them try again.
                print(str(e))
                wait_for_input()
                continue

            # Execute the functionality of each selected menu item.
            for item in [self.get_enumerated_items()[int(selection)] for selection in selections]:
                item.execute_function()
                if item.exit_action == "WAIT":
                    wait_for_input()
                elif item.exit_action == "BREAK":
                    return
                elif item.exit_action == "EXIT":
                    sys.exit(0)

class MenuItem:
    '''A MenuItem is a single selectable option of a Menu. Each MenuItem carries out some kind of
    function, which is the "function" argument in the constructor. This should be a Python function;
    when the MenuItem is selected, the function will get called with the list of args and the dict of
    kwargs provided in the constructor; if neither of these are provided, the function will be run
    with no arguments.

    To catch specific exceptions during the execution of this MenuItem's functionality, you can provide
    a list of exception types (e.g. exceptions_to_catch = [KeyError, sqlite3.OperationalError] .)
    If one of these exceptions occurs, the script will print out that an error occurred and wait for
    the user to press Enter to continue - but the script will not crash out; instead, the normal
    exit action will occur (typically just redrawing the menu).

    If the function you want to call requires custom input from the user, you can set requires_input
    to True; this will prompt the user for input (the text of the prompt comes from prompt_text),
    and passes the user's input as the first argument to the function. (Yes, this is a bit of a kludge.)

    The default behavior for a Menu, after executing a MenuItem, is to simply immediately re-display the menu.
    If you want to change this behavior, set the exit_action argument.
    - A value of "WAIT" will prompt the user to press Enter before the screen is cleared and
      the Menu is re-displayed; this is useful if this MenuItem is printing anything out to the screen
      that the user wants to see.
    - A value of "BREAK" will break out of the Menu's infinite loop, returning you to the Menu's parent.
    - A value of "EXIT" will exit the entire program immediately.
    Each Menu comes with options to do these last two things automatically, so you don't need to define your own.
    '''
    def __init__(self, menu, text, function, function_args = None, function_kwargs = None, exceptions_to_catch = None, requires_input = False, prompt_text = "", exit_action = None):
        self.menu = menu
        self.text = text
        self.function = function

        self.function_args = function_args if function_args else []
        self.function_kwargs = function_kwargs if function_kwargs else {}
        self.exceptions_to_catch = exceptions_to_catch if exceptions_to_catch else []

        self.requires_input = requires_input
        self.prompt_text = prompt_text

        self.exit_action = exit_action

    def execute_function(self):
        '''This executes the menu item's function, with any configured arguments.'''
        user_input = [input(self.prompt_text)] if self.requires_input else []

        try:
            self.function(*(user_input + self.function_args), **self.function_kwargs)
        except Exception as thrown_exception: # pylint: disable = broad-except
            if not [x for x in self.exceptions_to_catch if isinstance(thrown_exception, x)]:
                raise # If we weren't configured to safely catch this exception, raise it as normal.
            else:
                print(wrapper.fill(f"ERROR! When trying to execute the menu item '{self.text}', an error occurred."))
                print(wrapper.fill(f"The error message received was: {thrown_exception.__class__.__name__}: {thrown_exception!s}"))
                if self.exit_action != "WAIT": # The function's normal exit action will get called, so
                    wait_for_input() # if it's already going to make the user press Enter, don't do it twice.

        return self.exit_action

class MenuSeparator:
    '''A MenuSeparator is a dummy object that allows you to insert "separator" lines
    within a Menu's list of MenuItems. You may optionally provide some text to display;
    otherwise, the separator is simply represented by a blank line.'''
    def __init__(self, text = ""):
        self.text = text

def wait_for_input():
    '''This waits for the user to press Enter. Useful when the user
    needs to see some displayed text before it disappears.'''
    input("Press Enter to continue...")

def get_arguments():
    '''This handles the parsing of various arguments to the script.'''
    parser = argparse.ArgumentParser(description = "Connect to the F1 SQLite database (or reload it from the CSV files) and run queries against it.")
    parser.add_argument("-r", "--reload", action = "store_true")
    parser.add_argument("-d", "--download", action = "store_true")
    parser.add_argument("-q", "--quiet", action = "store_true")
    parser.add_argument("-v", "--verbose", action = "store_true")
    parser.add_argument("-s", "--execute_script", action = "store", nargs = "+")
    parser.add_argument("-t", "--export_table", action = "store", nargs = "+")
    parser.add_argument("-x", "--exit", action = "store_true")
    return parser.parse_args()

def handle_arguments(arguments):
    '''This executes some one-off functionality based on specific argument values.'''
    # The logging level gets instantiated to INFO, but it can be overridden by CLI arguments.
    if arguments.verbose:
        logger.setLevel(logging.DEBUG)
    elif arguments.quiet:
        logger.setLevel(logging.WARNING)

    if arguments.download:
        logger.debug("Download option provided; redownloading files")
        redownload_files()
    elif not os.path.exists(config.BASE_CSV_FILES_DIR) or not os.listdir(config.BASE_CSV_FILES_DIR):
        print(f"{config.BASE_CSV_FILES_DIR} missing or empty!")
        user_input = input("Do you want to redownload the CSV files from the source? [y/n]: ")
        if user_input.lower() in ["y", "yes"]:
            redownload_files()
        else:
            raise FileNotFoundError(f"./{config.BASE_CSV_FILES_DIR} missing or empty and user declined to redownload from source")

    if arguments.reload:
        logger.debug("Reload argument provided; reloading database")
        reload_database()

    if arguments.download and not arguments.reload:
        print("New CSV files downloaded from source, but -r/--reload not specified!")
        print("If you do not rebuild the database from these new CSV files,")
        print("any updates will not be reflected in the database.")
        user_input = input("Do you want to rebuild the database from the CSV files? [y/n]: ")
        if user_input.lower() in ["y", "yes"]:
            reload_database()

    if not os.path.exists(config.DATABASE_FILE_NAME):
        print(f"{config.DATABASE_FILE_NAME} not found!")
        user_input = input("Do you want to rebuild the database from the CSV files? [y/n]: ")
        if user_input.lower() in ["y", "yes"]:
            reload_database()
        else:
            raise FileNotFoundError(f"/{config.DATABASE_FILE_NAME} not found and user declined to rebuild from source")

    # Certain arguments require a Connection to the DB, and it's advantageous for them to share a connection.
    # Check if any of them are present and set up a Connection if so.
    if any([arguments.execute_script, arguments.export_table]):
        with Connection() as conn:
            conn.bind_queries(config.QUERY_YAML_FILE_NAME)

            for script_file in arguments.execute_script:
                conn.execute_sql_script_file(script_file)

            for table_name in arguments.export_table:
                conn.export_table_to_csv(table_name)

    if arguments.exit:
        logger.debug("Exit argument provided; exiting.")
        sys.exit(1)

def get_latest_grand_prix():
    '''This queries the Ergast API's endpoint shortcut for the most recent race
    and returns its season and name. Useful for checking see if new data is ready.'''
    race_json = requests.get("http://ergast.com/api/f1/current/last/results.json").json()
    race = race_json["MRData"]["RaceTable"]["Races"][0]
    print (f"The latest GP is the {race['season']} {race['raceName']}.")

def redownload_files():
    '''This handles the process of redownloading the CSV files from the Ergast website.'''
    # Create the CSV files directory if it doesn't already exist.
    if not os.path.exists(config.BASE_CSV_FILES_DIR):
        os.makedirs(config.BASE_CSV_FILES_DIR)

    # Clear out all of the existing CSV files.
    logger.debug(f"Clearing out {config.BASE_CSV_FILES_DIR }...")
    for file_name in os.listdir(config.BASE_CSV_FILES_DIR):
        if file_name.endswith(".csv"):
            os.remove(os.path.join(config.BASE_CSV_FILES_DIR, file_name))
    logger.debug("Files removed.")

    logger.info("Downloading CSV zip file from Ergast...")
    with open(os.path.join(config.BASE_CSV_FILES_DIR, config.ERGAST_ZIP_FILE_NAME), "wb") as downfile:
        for data in requests.get(config.ERGAST_DOWNLOAD_URL, stream = True).iter_content():
            downfile.write(data)
    logger.info("Download complete.")

    # Extract the zip file we downloaded to the CSV file directory.
    logger.info("Extracting CSV files...")
    with zipfile.ZipFile(os.path.join(config.BASE_CSV_FILES_DIR, config.ERGAST_ZIP_FILE_NAME), "r") as csv_zip:
        csv_zip.extractall(config.BASE_CSV_FILES_DIR)
    logger.info("Extraction complete.")

    # Remove the downloaded zip file.
    logger.debug("Removing the downloaded zip file...")
    os.remove(os.path.join(config.BASE_CSV_FILES_DIR, config.ERGAST_ZIP_FILE_NAME))
    logger.debug("Zip file removed.")

def reload_database():
    '''This function reloads the SQLite database from scratch. The database file is deleted,
    then it is rebuilt by running TABLE_DEFINITION_SCRIPT_FILE to define the base tables,
    then populate_base_tables() to populate them. Finally, RELOAD_SCRIPT_FILES is run,
    which defines and calculates a number of supplemental tables.

    In practice, this function gets called when the --reload argument is provided
    on the command line, or when the relevant menu option is selected.

    Yes, we could theoretically return the connection instead of spinning up a new one,
    but connections are cheap, and this helps keep the functions to a single responsibility.'''

    def populate_tables_from_csvs(connection, csv_file_dir):
        '''This function populates tables of the database from CSV files in a directory
        on disk. This must not be run until after the relevant tables have been defined.'''
        for file_name in os.listdir(csv_file_dir):
            with open(os.path.join(csv_file_dir, file_name), "r") as infile:
                reader = csv.DictReader(infile)
                records = [[record[field_name] if record[field_name] != r'\N' else None for field_name in reader.fieldnames] for record in reader]

            table_name = file_name.replace(".csv", "")
            field_names_tuple = re.sub(r'([a-z])([A-Z])', r'\1_\2', str(tuple(reader.fieldnames)).replace("'", "")).lower()
            question_marks_tuple = str(tuple(["?"] * len(reader.fieldnames))).replace("'", "")

            insert_statement = " ".join(["INSERT INTO", table_name, field_names_tuple, "VALUES", question_marks_tuple]) + ";"
            connection.connection.executemany(insert_statement, records)
            connection.connection.commit()

    if os.path.exists(config.DATABASE_FILE_NAME):
        os.remove(config.DATABASE_FILE_NAME) # Delete the SQLite database entirely

    with Connection() as connection:
        logger.debug("Defining base tables...")
        connection.execute_sql_script_file(config.BASE_TABLE_DEFINITION_SCRIPT_FILE)
        logger.debug("Base tables defined.")

        logger.info("Populating base tables...")
        populate_tables_from_csvs(connection, config.BASE_CSV_FILES_DIR)
        logger.info("Base tables populated.")

        logger.debug("Defining custom data tables...")
        connection.execute_sql_script_file(config.CUSTOM_TABLE_DEFINITION_SCRIPT_FILE)
        logger.debug("Custom data tables defined.")

        logger.info("Populating custom data tables...")
        populate_tables_from_csvs(connection, config.CUSTOM_CSV_FILES_DIR)
        logger.info("Custom data tables populated.")

        for script_file in config.RELOAD_SCRIPT_FILES:
            logger.info(f"Running {script_file}...")
            connection.execute_sql_script_file(script_file)
            logger.info(f"{script_file} run successfully.")

def define_menus(connection):
    '''This is a big POS kludge of a function that does the work of defining all of the menus
    for this program. This should really, really be outsourced somewhere, but it... sort of works
    for right now.'''
    # You need to define all of your Menus first, so that any MenuItems below can refer to them if they want.
    # For example, if you want a MenuItem to invoke a submenu, that submenu has to already exist as a variable.
    main_menu = Menu(connection, text = "Main menu.")
    queries_submenu = Menu(connection, parent_menu = main_menu, text = "Run any of the pre-defined queries below.")
    sql_scripts_submenu = Menu(connection, parent_menu = main_menu, text = "Run any of the SQL script files below.", allows_multi_select = True)

    main_menu.menu_items += [
        MenuItem(main_menu, "Ask the Ergast API what its latest Grand Prix is.", get_latest_grand_prix, exit_action = "WAIT"),
        MenuItem(
            main_menu,
            "Redownload the raw-data files from the Ergast API.",
            redownload_files,
            exit_action = None if logger.level == logging.WARNING else "WAIT"
        ),
        MenuItem(
            main_menu,
            "Rebuild the database from the raw-data files.",
            reload_database,
            exit_action = None if logger.level == logging.WARNING else "WAIT"
        ),
        MenuSeparator(),
        MenuItem(
            main_menu,
            "Execute a single SELECT statement and print its output.",
            main_menu.connection.print_select_results,
            exceptions_to_catch = [sqlite3.OperationalError],
            requires_input = True,
            prompt_text = "Enter your SELECT statement: ",
            exit_action = "WAIT"
        ),
        MenuItem(main_menu, "Execute the contents of a SQL script file.", sql_scripts_submenu.run),
        MenuItem(main_menu, "Run one or more pre-defined queries against the database.", queries_submenu.run),
        MenuItem(
            main_menu,
            "Export a table to a CSV file.",
            main_menu.connection.export_table_to_csv,
            exceptions_to_catch = [sqlite3.OperationalError],
            requires_input = True,
            prompt_text = "Enter the table name to be exported: "
        )
    ]

    for query in connection.queries:
        query_menu = Menu(connection, parent_menu = queries_submenu, text = query.name, allows_multi_select = True)
        queries_submenu.menu_items.append(MenuItem(queries_submenu, query.name, query_menu.run))
        query_menu.menu_items += [
            MenuItem(query_menu, "Run this query to calculate its results table.", query.calculate_results_table, exceptions_to_catch = [sqlite3.OperationalError]),
            MenuItem(query_menu, "Export this query's results table to a CSV.", query.export_table_to_csv),
            MenuSeparator()
        ]
        query_menu.menu_items += [
            MenuItem(query_menu, f"Export the {qviz.figure_type} chart titled {qviz.title} as a PNG.", qviz.export_png)
            for qviz in query.visualizations
        ]

    for script_file in [
        file for file in os.listdir(config.SQL_SCRIPT_FILES_DIR)
        if file not in [config.BASE_TABLE_DEFINITION_SCRIPT_FILE, config.CUSTOM_TABLE_DEFINITION_SCRIPT_FILE]
    ]:
        sql_scripts_submenu.menu_items.append(MenuItem(
            sql_scripts_submenu,
            script_file,
            connection.execute_sql_script_file,
            function_args = [script_file],
            exceptions_to_catch = [sqlite3.OperationalError]
        ))

    # Todo: Have some way to have the menus rebuild themselves.
    # The scripts and queries menu will not detect any new files.
    # Todo: Move this code somewhere sane instead of this POS.

    return (main_menu, queries_submenu, sql_scripts_submenu)

def main():
    '''Execute top-level functionality.'''

    args = get_arguments()
    handle_arguments(args)

    with Connection() as conn:
        conn.execute_sql_script_file("display_tables.sql")
        conn.bind_queries(config.QUERY_YAML_FILE_NAME)

        (main_menu, queries_submenu, sql_scripts_submenu) = define_menus(conn) # pylint: disable = unused-variable
        main_menu.run()

if __name__ == "__main__":
    main()