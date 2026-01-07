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

    column_name = db_schema["COLUMN_NAME"]

    hl7_column = hl7_dictionary["COLUMN_NAME"]

    db_schema_delete_extra_keys = []

    for key in column_name.keys():
        if key not in (hl7_column.keys()):
            db_schema_delete_extra_keys.append(key)
    for key in db_schema_delete_extra_keys:
        del column_name[key]

    # select the values holder from db schema for column
    values_holder = tuple(hl7_column.keys())

    # select the values from hl7 message ans assign to the values holder for column
    values = tuple(str(hl7_column[value]) for value in values_holder)

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
    column_name = db_schema["COLUMN_NAME"]
    condition = db_schema["CONDITION"]

    hl7_column = hl7_dictionary["COLUMN_NAME"]

    db_schema_delete_extra_keys = []

    for key in column_name.keys():
        if key not in (hl7_column.keys()):
            db_schema_delete_extra_keys.append(key)

        # if key in (condition.keys()):
        #     db_schema_delete_extra_keys.append(key)
        #     # delete where state volumn from db schema nad hl7 becouse we don't need to update it allready exists
        #     del hl7_column[key]

    for key in db_schema_delete_extra_keys:
        # delete the extra data that didn't have value
        del column_name[key]

    # select the values holder from db schema for column
    column_values_holder = tuple(hl7_column.keys())
    # select the values from hl7 message ans assign to the values holder for column
    colmun_values = (str(hl7_column[value]) for value in column_values_holder)

    hl7_msg_conditions = hl7_dictionary["CONDITION"]
    # select the values holder from db schema for condition
    condition_values_holder = condition.keys()
    # select the values from hl7 message ans assign to the values holder for condition
    condition_values = (
        str(hl7_msg_conditions[value]) for value in condition_values_holder
    )

    values = tuple(colmun_values) + tuple(condition_values)

    set_clause = ",".join([f"{value} = ?" for value in column_name.values()])

    condition_strings = [f"{value} = ? " for key, value in condition.items()]
    condition = "" + "and ".join(condition_strings)

    sql = f"UPDATE [dbo].{table_name} SET {set_clause} WHERE {condition};"

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
    # select the values from hl7 message ans assign to the values holder
    values = tuple(str(hl7_column[value]) for value in values_holder)

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

    # select the values from hl7 message ans assign to the values holder
    values = tuple(str(hl7_column[value]) for value in values_holder)

    condition_strings = [f"{value} = ?" for key, value in condition.items()]

    condition = "" + " and ".join(condition_strings)

    sql = f"DELETE FROM [dbo].{table_name} WHERE {condition};"

    data = (sql, values)

    return querie_exe(data)


async def exec_procedure_for(db_schema: dict, values: dict):
    """
    Executes a stored procedure with the provided parameters.

    Args:
        db_schema (dict): A dictionary containing the procedure name and parameters.
        values (dict): A dictionary of parameter values.

    Returns:
        The result of the stored procedure execution.
    """

    # Extract the procedure name and parameters from the schema
    procedure_name = db_schema["PROCEDURE_NAME"]
    parameters = db_schema["PARAMETERS"]

    # Construct the parameter string for the EXEC query
    parameters_string = ", ".join([f"@{param} = ?" for param in parameters])

    # Construct the SQL query
    sql = f"EXEC {procedure_name} {parameters_string}"

    # Prepare the parameter values in the correct order
    value = [values.get(param) for param in parameters]

    # Convert empty strings to None (NULL in SQL)
    value = tuple(None if v == "" else v for v in value)

    data = (sql, value)

    return querie_exe(data)
