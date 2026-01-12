
import os
import pyodbc
from database.sqlconnection import get_db_connection, SOURCE
from log.logger import log_info, log_error

def get_sql_priority_from_content(content):
    """
    Determines execution priority based on uppercase content.
    """
    content_upper = content.upper()
    if 'CREATE TABLE' in content_upper:
        return 0
    if any(k in content_upper for k in ['ALTER TABLE', 'CREATE PROCEDURE', 'CREATE OR ALTER PROCEDURE', 'CREATE FUNCTION', 'CREATE VIEW']):
        return 1
    return 2

def setup_database_schema():
    """
    Sets up and verifies the database schema by executing all SQL scripts.
    Optimized to read files once and sort based on pre-calculated priority.
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

        sql_data = []
        for root, _, files in os.walk(base_sql_dir):
            for file in files:
                if file.endswith('.sql'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        priority = get_sql_priority_from_content(content)
                        sql_data.append({
                            'path': file_path,
                            'name': file,
                            'content': content,
                            'priority': priority
                        })
                    except Exception as e:
                        log_error(f"Error reading {file}: {e}", source=SOURCE)

        if not sql_data:
            log_info("No SQL files found for schema setup.", source=SOURCE)
            return

        # Sort files based on pre-calculated priority
        sql_data.sort(key=lambda x: x['priority'])

        log_info("Execution order of SQL files:")
        for item in sql_data:
            log_info(f"- {item['name']} (Priority: {item['priority']})")

        for item in sql_data:
            try:
                # Split the script into individual commands, separated by 'GO'
                sql_commands = item['content'].split('GO')
                for command in sql_commands:
                    if command.strip():
                        cursor.execute(command)
                log_info(f"Successfully executed {item['name']}", source=SOURCE)
            except Exception as e:
                log_error(f"Error executing {item['name']}: {e}", source=SOURCE)
                raise
        
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
