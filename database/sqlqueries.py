import copy
import asyncio
from database.sqlqueriesExe import querie_exe
from hl7msghandel.hl7fitsql import update_hl7_dictionary
from database.sqlconnection import get_db_connection


SOURCE = "Database"


def data_insert_for(
    db_schema: dict, hl7_dictionary: dict, hl7_message, sql_data=None, manual_data=None
):
    """
    this function generates an SQL query for inserting data into a table.
    The function takes a database connection object and a database schema dictionary as input.
    The function returns None that mean the job is done.

    Args:
        connection (object): The database connection object.
        db_schema (dict): A dictionary containing the database schema dictionary as input.

    Returns:
        None: This function does not return any value. It simply executes the SQL query and returns the None value.

    """

    hl7_dictionary = update_hl7_dictionary(
        hl7_message, hl7_dictionary, sql_data, manual_data
    )

    table_name = db_schema["TABLE_NAME"]

    # Protect global schema dictionary from in-place mutation
    column_name = copy.deepcopy(db_schema["COLUMN_NAME"])

    hl7_column = hl7_dictionary["COLUMN_NAME"]

    # Filter to only the columns present in the incoming hl7 message
    column_name = {
        key: col_db_name
        for key, col_db_name in column_name.items()
        if key in hl7_column
    }

    # select the values holder from db schema for column
    values_holder = tuple(column_name.keys())

    # select the values from hl7 message and assign to the values holder (preserve None as SQL NULL)
    values = tuple(
        None if hl7_column[value] is None or hl7_column[value] == "None"
        else str(hl7_column[value])
        for value in values_holder
    )

    columns = ", ".join(column_name.values())
    placeholders = ", ".join(["?" for _ in column_name])
    sql = f"INSERT INTO [dbo].{table_name} ({columns}) VALUES ({placeholders});"

    data = (sql, values)

    return querie_exe(data)


def data_update_for(
    db_schema: dict, hl7_dictionary: dict, hl7_message, sql_data=None, manual_data=None
):
    """
    this function generates an SQL query for updating data in a table.
    The function takes a database connection object and a database schema dictionary as input.
    The function returns None that mean the job is done.
    Args:
        connection (object): The database connection object.
        db_schema (dict): A dictionary containing the database schema dictionary as input.
    Returns:
        None: This function does not return any value. It simply executes the SQL query and returns the None value.
    """
    hl7_dictionary = update_hl7_dictionary(
        hl7_message, hl7_dictionary, sql_data, manual_data
    )

    table_name = db_schema["TABLE_NAME"]

    # Protect global schema dictionary from in-place mutation
    column_name = copy.deepcopy(db_schema["COLUMN_NAME"])
    condition = copy.deepcopy(db_schema["CONDITION"])

    hl7_column = hl7_dictionary["COLUMN_NAME"]

    # Filter to only the columns present in the incoming hl7 message
    column_name = {
        key: col_db_name
        for key, col_db_name in column_name.items()
        if key in hl7_column
    }

    # select the values holder from db schema for column
    column_values_holder = tuple(column_name.keys())
    # select the values from hl7 message and assign to the values holder (preserve None as SQL NULL)
    colmun_values = tuple(
        None if hl7_column[value] is None or hl7_column[value] == "None"
        else str(hl7_column[value])
        for value in column_values_holder
    )

    hl7_msg_conditions = hl7_dictionary["CONDITION"]
    # select the values holder from db schema for condition
    condition_values_holder = tuple(condition.keys())
    # select the values from hl7 message and assign to the values holder
    condition_values = tuple(
        None if hl7_msg_conditions[value] is None or hl7_msg_conditions[value] == "None"
        else str(hl7_msg_conditions[value])
        for value in condition_values_holder
    )

    values = colmun_values + condition_values

    set_clause = ", ".join([f"{value} = ?" for value in column_name.values()])

    condition_strings = [f"{value} = ?" for key, value in condition.items()]
    condition_clause = " and ".join(condition_strings)

    sql = f"UPDATE [dbo].{table_name} SET {set_clause} WHERE {condition_clause};"

    data = (sql, values)

    return querie_exe(data)


def data_select_for(
    db_schema: dict, hl7_dictionary: dict, hl7_message, sql_data=None, manual_data=None
):
    """
    this function generates an SQL query for selecting data from a table.
    The function takes a database connection object and a database schema dictionary as input.
    The function returns the select value from select query.
    Args:
        connection (object): The database connection object.
        db_schema (dict): A dictionary containing the database schema dictionary as input.
    Returns:
        select_value: The select value from select query.
    """

    hl7_dictionary = update_hl7_dictionary(
        hl7_message, hl7_dictionary, sql_data, manual_data
    )

    # select the table name from db schema
    table_name = db_schema["TABLE_NAME"]

    # select the column name from db schema
    column_name = db_schema["COLUMN_NAME"]

    # select the selected value variable from db schema
    selected_value_variable = tuple(column_name.keys())

    # select the condition data from db schema
    condition = db_schema["CONDITION"]

    # select the target value from hl7 message
    hl7_column = hl7_dictionary["CONDITION"]

    # select the values holder from db schema
    values_holder = tuple(condition.keys())
    # select the values from hl7 message and assign to the values holder (preserve None as SQL NULL)
    values = tuple(
        None if hl7_column[value] is None or hl7_column[value] == "None"
        else str(hl7_column[value])
        for value in values_holder
    )

    set_clause = ", ".join([f"{value}" for value in column_name.values()])

    condition_strings = [f"{value} = ?" for key, value in condition.items()]

    condition = "" + " and ".join(condition_strings)

    sql = f"SELECT {set_clause} FROM [dbo].{table_name} WHERE {condition};"

    data = (sql, values, selected_value_variable)

    return querie_exe(data)


def data_delete_for(
    db_schema: dict, hl7_dictionary: dict, hl7_message, sql_data=None, manual_data=None
):
    """
    this function generates an SQL query for deleting data from a table.
    The function takes a database connection object and a database schema dictionary as input.
    The function returns None that mean the job is done.
    Args:
        connection (object): The database connection object.
        db_schema (dict): A dictionary containing the database schema dictionary as input.
    Returns:
        None: This function does not return any value. It simply executes the SQL query and returns the None value.
    """

    hl7_dictionary = update_hl7_dictionary(
        hl7_message, hl7_dictionary, sql_data, manual_data
    )

    table_name = db_schema["TABLE_NAME"]
    condition = db_schema["CONDITION"]

    # select the target value from hl7 message
    hl7_column = hl7_dictionary["CONDITION"]

    # select the values holder from db schema
    values_holder = tuple(condition.keys())

    # select the values from hl7 message and assign to the values holder (preserve None as SQL NULL)
    values = tuple(
        None if hl7_column[value] is None or hl7_column[value] == "None"
        else str(hl7_column[value])
        for value in values_holder
    )

    condition_strings = [f"{value} = ?" for key, value in condition.items()]

    condition = "" + " and ".join(condition_strings)

    sql = f"DELETE FROM [dbo].{table_name} WHERE {condition};"

    data = (sql, values)

    return querie_exe(data)


def exec_procedure_sync(db_schema: dict, values: dict):
    """
    Synchronously executes a stored procedure with the provided parameters.

    Args:
        db_schema (dict): A dictionary containing the procedure name and parameters.
        values (dict): A dictionary of parameter values.

    Returns:
        The result of the stored procedure execution.
    """
    procedure_name = db_schema["PROCEDURE_NAME"]
    parameters = db_schema["PARAMETERS"]

    parameters_string = ", ".join([f"@{param} = ?" for param in parameters])
    sql = f"EXEC {procedure_name} {parameters_string}"

    value = [values.get(param) for param in parameters]
    value = tuple(None if v == "" else v for v in value)

    data = (sql, value)
    return querie_exe(data)


def exec_procedure_no_return_sync(db_schema: dict, values: dict):
    """
    Synchronously executes a stored procedure that does not return a result set.
    """
    procedure_name = db_schema["PROCEDURE_NAME"]
    parameters = db_schema["PARAMETERS"]

    parameters_string = ", ".join([f"@{param} = ?" for param in parameters])
    sql = f"EXEC {procedure_name} {parameters_string}"

    value_list = [values.get(param) for param in parameters]
    value_tuple = tuple(None if v == "" else v for v in value_list)

    data = (sql, value_tuple)
    querie_exe(data, expect_results=False)
    return None


async def exec_procedure_for(db_schema: dict, values: dict):
    """
    Asynchronously executes a stored procedure on a thread pool to avoid blocking the GUI event loop.
    """
    return await asyncio.to_thread(exec_procedure_sync, db_schema, values)


async def exec_procedure_no_return(db_schema: dict, values: dict):
    """
    Asynchronously executes a non-returning stored procedure on a thread pool.
    """
    return await asyncio.to_thread(exec_procedure_no_return_sync, db_schema, values)
