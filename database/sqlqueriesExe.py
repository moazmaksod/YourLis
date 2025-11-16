from log.logger import log_info, log_error
from database.sqlconnection import get_db_connection


SOURCE = "Database"


def querie_exe(data, expect_results=True):
    """
    Executes the provided SQL query with the given values. Handles SELECT, INSERT, UPDATE, and DELETE queries.

    Args:
        data (tuple): A tuple containing the SQL query and the values to be inserted, updated, fetched, or deleted.
                      Example: (query, values)
        expect_results (bool): Whether to expect a result set from the query. Defaults to True.

    Returns:
        result (dict or None):
            - For SELECT queries, returns a dictionary with column names as keys and corresponding values from the first row as values.
            - For non-SELECT queries (INSERT, UPDATE, DELETE), returns None after committing the transaction.
    """
    log_info("Starting query execution.", source=SOURCE)

    # Establish database connection
    connection = get_db_connection()
    sql = data[0]
    values = data[1]
    cursor = connection.cursor()

    try:
        # Execute the SQL query
        cursor.execute(sql, values)

        # If it's a SELECT query, fetch the results
        if sql.strip().upper().startswith("SELECT"):
            selected_value_variable = data[2]
            selected_value = {}
            results = cursor.fetchall()
            log_info(
                f"Executed SELECT query: {sql} with values: {values}", source=SOURCE
            )
            if results:
                # Assuming the first row contains the result we want to map to variables
                selected_value = {
                    var: item for var, item in zip(selected_value_variable, results[0])
                }
                return selected_value

            log_info("No results returned for SELECT query.", source=SOURCE)
            return None  # Return None if no results found

        # For EXEC queries, handle based on whether results are expected
        elif sql.strip().upper().startswith("EXEC"):
            if expect_results:
                results = cursor.fetchall()
                log_info(f"Executed EXEC query: {sql} with values: {values}", source=SOURCE)

                if results:
                    # Fetch the results as a list of dictionaries
                    columns = [column[0] for column in cursor.description]
                    result_dicts = []

                    for row in results:
                        result_dict = {columns[i]: row[i] for i in range(len(columns))}
                        result_dicts.append(result_dict)
                    return result_dicts

                log_info("No results returned for EXEC query.", source=SOURCE)
                return None  # Return None if no results found
            else:
                # For EXEC that doesn't return results, just commit
                connection.commit()
                log_info(f"Executed non-result EXEC query: {sql} with values: {values}", source=SOURCE)
                return None

        else:
            # For INSERT, UPDATE, DELETE, commit the transaction
            connection.commit()
            log_info(
                f"Executed non-SELECT query: {sql} with values: {values}", source=SOURCE
            )
            return None

    except Exception as e:
        # Log error and rollback in case of an exception
        log_error(
            f"Error executing query: {sql} with values: {values}. Error: {e}",
            source=SOURCE,
        )
        connection.rollback()  # Rollback in case of error
        return None

    finally:
        cursor.close()  # Ensure the cursor is closed
        # Optionally, close the connection here if it's not needed anymore
        connection.close()  # Uncomment if you want to close the connection after each query
        log_info("Query execution finished.", source=SOURCE)
