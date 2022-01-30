#! /usr/bin/env/python3
'''This file contains definitions for all UDFs (User-Defined Functions) that
will be compiled and made available for use each time a connection is instantiated.

Per the sqlite3 documentation, UDFs are defined by passing a Python "udf object" (a class or function)
as an argument to a method of a sqlite3 Connection. Scalar functions require a Python function,
and aggregation functions require a Python class with __init__, step, and finalize class methods.
The sqlite3 library will then call the provided "udf object" to implement its functionality.

In other words, the user is responsible for developing the logic to get the function to work,
and exposing the appropriate interfaces for the sqlite3 Connection to make use of it.
This file, then, is an all-in-one-place list of all of these function definitions for the F1DB project.

To add UDFs to this file, simply add the requisite class/function definitions to the file below.
See https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.create_function for more details.

Your class/function name MUST be named the same as the callable name of the SQL function you want
to define, and its Python function name MUST begin with "udf_"!

For example, if you want to define a UDF that can be called in SQL as "MY_FUNCTION(foo, bar, baz)",
then you will need to define it in this file as "def udf_my_function(foo, bar, baz):".
This allows the dict comprehension at the bottom of this file to detect and parse your UDF correctly
so that it can store all of the information needed to compile the function at a later time.

When this file is imported ("import f1db_udfs"), the list of UDFs can be accessed under the name
"f1db_udfs.USER_DEFINED_FUNCTIONS", which yields the list of dicts at the bottom of this file.
'''
import inspect, math, statistics, time
import pdb # pylint: disable = unused-import

def udf_power(base, exponent):
    '''This UDF implements power (i.e. exponent) calculation.'''
    return base ** exponent

def udf_sqrt(base):
    '''This UDF implements square-root calculation.'''
    return math.sqrt(base)

def udf_ms_to_hhmmss(milliseconds):
    '''This UDF takes in an integer number of milliseconds and returns the formatted string
    of the milliseconds represented as hours:minutes:seconds. Useful for "total time" ms values.'''
    return time.strftime("%H:%M:%S", time.gmtime(milliseconds / 1000))

class udf_stdev: # pylint: disable = missing-function-docstring
    '''This UDF implements standard-deviation calculation.
    Note that this is the SAMPLE stdev; for the POPULATION stdev, use STDEV_POP.'''
    def __init__(self):
        self.values = []

    def step(self, value):
        if isinstance(value, (int, float)):
            self.values.append(value)

    def finalize(self):
        return statistics.stdev(self.values)

class udf_stdev_pop: # pylint: disable = missing-function-docstring
    '''This UDF implements standard-deviation calculation.
    Note that this is the POPULATION stdev; for the SAMPLE stdev, use STDEV.'''
    def __init__(self):
        self.values = []

    def step(self, value):
        if isinstance(value, (int, float)):
            self.values.append(value)

    def finalize(self):
        return statistics.pstdev(self.values)

USER_DEFINED_FUNCTIONS = [{
    "udf_name": object_name.replace("udf_", "").upper(), # Converts "udf_myfunc" to "MYFUNC"
    "udf_type": "Aggregation" if inspect.isclass(udf_object) else "Scalar",
    "num_arguments": 1 if inspect.isclass(udf_object) else len(inspect.signature(udf_object).parameters),
    "udf_object": udf_object
} for object_name, udf_object in locals().items() if object_name[:4] == "udf_"]