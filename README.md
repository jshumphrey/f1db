# f1db

This Python code maintains a SQLite database of Formula One race data, and provides some functionality to facilitate the process of running queries against it, and visualizing the output of those queries.

## Requirements

You'll need these Python modules installed. On Linux, some or all of these might be available from your distro's package manager; if you're not on Linux or they're not available, you can always get them from  `pip`.

- `kaleido`
- `pandas`
- `plotly`
- `pyyaml`
- `requests`

(Proper requirements.txt coming soon.)

## Running the program

Run `f1db.py` from the command line. (Right now, the command line just dumps you at the debug console, so you'll need to read the code to find out what objects and functions are available. A proper menu for commands is coming soon.)

### Command-line arguments

#### Functional

- `-r`, `--reload`: Delete the SQLite database file, and regenerate it from the downloaded CSV files.
- `-d`, `--download`: Download a fresh copy of the CSV files from the Ergast API. Also rebuilds the database, as per `--reload`.
  - You'll want to do this if you're expecting the Ergast data to have changed, such as after the completion of a Grand Prix.
  - If this is your first time running the program, you'll need to specify this argument so that the program has raw-data files to work with.

#### Logging

- `-q`, `--quiet`: Suppress all logging/informational output, except for error messages.
- `-v`, `--verbose`: Display additional debug output.

## Maintaining the program

To adjust any of the configuration parameters, all of them are set in [f1db_config.py](f1db_config.py).

To add new user-defined functions to the SQLite interface, look at [the code file for f1db_udfs.py](f1db_udfs.py) - it's pretty self-documenting.

To add new query/chart definitions, look at the code in f1db.py for the Query and QueryVisualization class, and then look through [the YAML file of query definitions](f1db_queries.yml).

## Source of the raw Formula One data

Major credit goes to the Ergast API, the host of the raw Formula One race data that this code uses. None of this would have been possible without good data to work with.

See http://ergast.com/mrd/ for more details about the API and the table structure.

## Database table structure

The author of the Ergast API provided two documents on the database table structure, which I've included here for reference. See [data_dictionary.txt](data_dictionary.txt) and [data_model.png](data_model.png).

**In addition to this**, there are a number of custom or extended tables that have been defined via the supplemental SQL files. Look at `RELOAD_SCRIPT_FILES` in [f1db_config.py](f1db_config.py) to see what else is defined.