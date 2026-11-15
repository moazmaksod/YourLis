import pyodbc
from log.logger import log_info, log_error, sanitize_parameters
from database.sqlconnection import get_db_connection_context

SOURCE = "Database"


def querie_exe(data, expect_results=True, return_all=False):
    """
    Executes the provided SQL query with the given values. Handles SELECT, INSERT, UPDATE, and DELETE queries.
    Acquires and returns connections via a thread-safe connection pool, preventing connection leaks.

    Args:
        data (tuple): A tuple containing the SQL query and the values to be inserted, updated, fetched, or deleted.
                      Example: (query, values)
        expect_results (bool): Whether to expect a result set from the query. Defaults to True.
        return_all (bool): For SELECT queries, whether to return all matching rows as a list of dicts.
                           Defaults to False (returns a dict for the first row).

    Returns:
        result (dict, list or None):
            - For SELECT queries with return_all=False, returns a dictionary with column names as keys
              and corresponding values from the first row.
            - For SELECT queries with return_all=True, returns a list of dictionaries for all matching rows.
            - For non-SELECT queries (INSERT, UPDATE, DELETE), returns None after committing the transaction.
    """
    log_info("Starting query execution.", source=SOURCE)
    sql = data[0]
    values = data[1]

    with get_db_connection_context() as connection:
        cursor = connection.cursor()
        try:
            # Execute the SQL query
            cursor.execute(sql, values)

            # If it's a SELECT query, fetch the results
            if sql.strip().upper().startswith("SELECT"):
                selected_value_variable = data[2]
                results = cursor.fetchall()
                log_info(
                    f"Executed SELECT query: {sql} with {len(values)} parameter(s)",
                    source=SOURCE,
                )
                if results:
                    if return_all:
                        return [
                            {var: item for var, item in zip(selected_value_variable, row)}
                            for row in results
                        ]
                    selected_value = {
                        var: item for var, item in zip(selected_value_variable, results[0])
                    }
                    return selected_value

                log_info("No results returned for SELECT query.", source=SOURCE)
                return None

            # For EXEC queries, handle based on whether results are expected
            elif sql.strip().upper().startswith("EXEC"):
                if expect_results:
                    _max_sets = 50
                    while cursor.description is None and cursor.nextset() and _max_sets > 0:
                        _max_sets -= 1
                    if cursor.description:
                        results = cursor.fetchall()
                        log_info(
                            f"Executed EXEC query: {sql} with {len(values)} parameter(s)",
                            source=SOURCE,
                        )
                        connection.commit()

                        if results:
                            columns = [column[0] for column in cursor.description]
                            result_dicts = []
                            for row in results:
                                result_dict = {columns[i]: row[i] for i in range(len(columns))}
                                result_dicts.append(result_dict)
                            return result_dicts

                        log_info("No results returned for EXEC query.", source=SOURCE)
                        return None
                    else:
                        connection.commit()
                        log_info("No result set available for EXEC query.", source=SOURCE)
                        return None
                else:
                    # For EXEC that doesn't return results, commit the transaction
                    connection.commit()
                    log_info(
                        f"Executed non-result EXEC query: {sql} with {len(values)} parameter(s)",
                        source=SOURCE,
                    )
                    return None

            else:
                # For INSERT, UPDATE, DELETE, commit the transaction
                connection.commit()
                log_info(
                    f"Executed non-SELECT query: {sql} with {len(values)} parameter(s)",
                    source=SOURCE,
                )
                return None

        except Exception as e:
            # Mask parameter details in error logs to protect PHI
            masked_params = sanitize_parameters(values)
            log_error(
                f"Error executing query: {sql} with parameters: {masked_params}. Error: {e}",
                source=SOURCE,
            )
            try:
                connection.rollback()
            except Exception:
                pass
            raise

        finally:
            cursor.close()
            log_info("Query execution finished.", source=SOURCE)
