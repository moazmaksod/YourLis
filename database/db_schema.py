
import os
import pyodbc
from database.sqlconnection import get_db_connection, SOURCE
from log.logger import log_info, log_error

def get_sql_file_priority(file_path):
    """
    Determines the execution priority of a SQL file based on its content.
    Priority 0: Table creations.
    Priority 1: Alters, procedures, functions, views.
    Priority 2: Data modifications, other scripts.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().upper()
        
        if 'CREATE TABLE' in content:
            return 0
        if 'ALTER TABLE' in content or 'CREATE PROCEDURE' in content or \
           'CREATE OR ALTER PROCEDURE' in content or 'CREATE FUNCTION' in content or \
           'CREATE VIEW' in content:
            return 1
        return 2
    except Exception as e:
        log_error(f"Error reading {os.path.basename(file_path)} for priority: {e}", source=SOURCE)
        return 100 # High number to push it to the end

def execute_sql_file(cursor, file_path):
    """
    Executes the SQL commands from a given file.
    Splits the script by 'GO' to handle batch operations.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Split the script into individual commands, separated by 'GO'
        sql_commands = sql_script.split('GO')
        
        for command in sql_commands:
            if command.strip():
                cursor.execute(command)
        
        log_info(f"Successfully executed {os.path.basename(file_path)}", source=SOURCE)
        return True
    except Exception as e:
        log_error(f"Error executing {os.path.basename(file_path)}: {e}", source=SOURCE)
        # Re-raise the exception to be caught by the caller
        raise

def setup_database_schema():
    """
    Sets up and verifies the database schema by executing all SQL scripts
    found in the 'Sql_reqirement_querys' subdirectories.
    It intelligently sorts the scripts to ensure tables are created before
    procedures and other objects.
    """
    log_info("Starting database schema setup and verification...", source=SOURCE)
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        base_sql_dir = os.path.join(os.path.dirname(__file__), '..', 'Sql_reqirement_querys')
        
        if not os.path.exists(base_sql_dir):
            log_info(f"SQL requirements directory not found at: {base_sql_dir}. Skipping schema setup.", source=SOURCE)
            return

        sql_files = []
        for root, _, files in os.walk(base_sql_dir):
            for file in files:
                if file.endswith('.sql'):
                    sql_files.append(os.path.join(root, file))

        if not sql_files:
            log_info("No SQL files found for schema setup.", source=SOURCE)
            return

        # Sort files based on content to ensure correct execution order
        sorted_files = sorted(sql_files, key=get_sql_file_priority)

        log_info("Execution order of SQL files:")
        for f in sorted_files:
            log_info(f"- {os.path.basename(f)}")

        for sql_file in sorted_files:
            execute_sql_file(cursor, sql_file)
        
        connection.commit()
        log_info("Database schema setup and verification finished successfully.", source=SOURCE)
        
    except Exception as e:
        if connection:
            try:
                connection.rollback()
                log_info("Database transaction rolled back due to an error.", source=SOURCE)
            except pyodbc.Error as rb_ex:
                log_error(f"Error during rollback: {rb_ex}", source=SOURCE)
        
        log_error(f"Database schema setup failed: {e}", source=SOURCE)
        # Re-raise the exception to notify the caller of the failure
        raise
    
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    # This allows running the setup directly for testing or manual setup
    try:
        setup_database_schema()
    except Exception as e:
        print(f"Schema setup failed. Please check the logs. Error: {e}")
