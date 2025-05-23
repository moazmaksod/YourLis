import pyodbc
from typing import Dict, List, Any, Union, Tuple, Optional # Added Optional
from log.logger import log_info, log_error, log_warning # For logging

from database.database_adapter import DatabaseAdapter
from database.sqlconnection import get_db_connection
from database import sqldbdictionary
# sqlqueriesExe and sqlqueries are removed as per plan to use direct cursor execution or integrate logic.

SOURCE_CONTEXT = "MssqlAdapter" # For logging

class MssqlAdapter(DatabaseAdapter):
    """
    MSSQL Database Adapter.
    Implements the DatabaseAdapter interface for Microsoft SQL Server.
    """

    def __init__(self) -> None:
        self.connection: Union[pyodbc.Connection, None] = None
        self.cursor: Union[pyodbc.Cursor, None] = None

        # Schema definitions from sqldbdictionary
        # RESULT_EXIST_SQL related attributes
        self.result_exist_table_name = sqldbdictionary.RESULT_EXIST_SQL["TABLE_NAME"]
        self.result_exist_patient_id_col = sqldbdictionary.RESULT_EXIST_SQL["COLUMN_NAME"]["PATIENT_ID"]
        self.result_exist_condition_pid_col = sqldbdictionary.RESULT_EXIST_SQL["CONDITION"]["PATIENT_ID"]


        # CBC_RESULT_SQL related attributes
        self.cbc_table_name = sqldbdictionary.CBC_RESULT_SQL["TABLE_NAME"]
        self.cbc_sql_column_definitions = sqldbdictionary.CBC_RESULT_SQL["COLUMN_NAME"]
        self.cbc_sql_patient_id_col = self.cbc_sql_column_definitions["PATIENT_ID"]
        self.cbc_sql_request_date_col = self.cbc_sql_column_definitions["REQ_DATE"]
        # Generic key (e.g. 'HGB') to SQL column name (e.g. '[hgb]')
        self.cbc_generic_to_sql_map: Dict[str, str] = {}
        self.cbc_sql_to_generic_map: Dict[str, str] = {}
        self._dynamic_populate_cbc_map_from_sqldict()

        # HGB_RESULT_SQL related attributes
        # Note: HGB results are stored in the same table as CBC results per sqldbdictionary
        self.hgb_table_name = sqldbdictionary.HGB_RESULT_SQL["TABLE_NAME"] # Should be same as cbc_table_name
        self.hgb_sql_column_definitions = sqldbdictionary.HGB_RESULT_SQL["COLUMN_NAME"]
        self.hgb_sql_patient_id_col = self.hgb_sql_column_definitions["PATIENT_ID"]
        self.hgb_sql_request_date_col = self.hgb_sql_column_definitions["REQ_DATE"]
        self.hgb_generic_to_sql_map: Dict[str, str] = {}
        self.hgb_sql_to_generic_map: Dict[str, str] = {}
        self._dynamic_populate_hgb_map_from_sqldict()

        # PATIENT_INFO_SQL related attributes
        self.patient_info_table_name = sqldbdictionary.PATIENT_INFO_SQL["TABLE_NAME"]
        self.patient_info_sql_column_definitions = sqldbdictionary.PATIENT_INFO_SQL["COLUMN_NAME"]
        self.patient_info_condition_pid_col = sqldbdictionary.PATIENT_INFO_SQL["CONDITION"]["PATIENT_ID"]
        # Map for SQL col name to generic key for patient info
        self.patient_info_sql_to_generic_map = {
            sql_col: generic_key for generic_key, sql_col in self.patient_info_sql_column_definitions.items()
        }


        # PATIENT_TEST_SQL related attributes
        self.patient_test_table_name = sqldbdictionary.PATIENT_TEST_SQL["TABLE_NAME"]
        self.patient_test_sql_column_definitions = sqldbdictionary.PATIENT_TEST_SQL["COLUMN_NAME"]
        self.patient_test_condition_pid_col = sqldbdictionary.PATIENT_TEST_SQL["CONDITION"]["PATIENT_ID"]
         # Map for SQL col name to generic key for patient test requests
        self.patient_test_sql_to_generic_map = {
            sql_col: generic_key for generic_key, sql_col in self.patient_test_sql_column_definitions.items()
        }

        # Stored Procedure names
        self.patient_search_proc_name = sqldbdictionary.PATIENT_SEARCH_SQL["PROCEDURE_NAME"]
        self.patient_search_proc_params = sqldbdictionary.PATIENT_SEARCH_SQL["PARAMETERS"]
        self.patient_cbc_result_proc_name = sqldbdictionary.PATIENT_CBC_RESULT_SQL["PROCEDURE_NAME"]
        self.patient_cbc_result_proc_params = sqldbdictionary.PATIENT_CBC_RESULT_SQL["PARAMETERS"]


    def _dynamic_populate_cbc_map_from_sqldict(self) -> None:
        """Populates CBC mapping dictionaries from sqldbdictionary.CBC_RESULT_SQL."""
        # Generic keys are the keys from COLUMN_NAME dict (e.g. 'HGB', 'RBC')
        # SQL column names are the values (e.g. '[hgb]', '[rbc]')
        self.cbc_generic_to_sql_map = {
            key: sql_col_name
            for key, sql_col_name in self.cbc_sql_column_definitions.items()
            # Exclude PATIENT_ID and REQ_DATE from this specific map if they are handled separately
            # However, the adapter methods expect them in result_data for save/update sometimes.
            # For now, include all.
        }
        self.cbc_sql_to_generic_map = {v: k for k, v in self.cbc_generic_to_sql_map.items()}
        if not self.cbc_generic_to_sql_map:
            log_warning("CBC generic_to_sql_map is empty after population attempt.", source=SOURCE_CONTEXT)

    def _dynamic_populate_hgb_map_from_sqldict(self) -> None:
        """Populates HGB mapping dictionaries from sqldbdictionary.HGB_RESULT_SQL."""
        self.hgb_generic_to_sql_map = {
            key: sql_col_name
            for key, sql_col_name in self.hgb_sql_column_definitions.items()
        }
        self.hgb_sql_to_generic_map = {v: k for k, v in self.hgb_generic_to_sql_map.items()}
        if not self.hgb_generic_to_sql_map:
            log_warning("HGB generic_to_sql_map is empty after population attempt.", source=SOURCE_CONTEXT)


    def connect(self, connection_params: Dict[str, Any]) -> None:
        """
        Establishes a connection to the database.
        connection_params are currently ignored as config.py is used by get_db_connection.
        """
        try:
            self.connection = get_db_connection()
            if self.connection:
                self.cursor = self.connection.cursor()
                # Maps are populated in __init__ now.
                log_info("Successfully connected to the database.", source=SOURCE_CONTEXT)
            else:
                # Handle connection failure, maybe raise an exception
                log_error("Failed to establish database connection: get_db_connection returned None.", source=SOURCE_CONTEXT)
                raise ConnectionError("Failed to establish database connection.")
        except pyodbc.Error as ex:
            sqlstate = ex.args[0]
            log_error(f"Database connection failed with SQLState {sqlstate}: {ex}", source=SOURCE_CONTEXT)
            raise ConnectionError(f"Database connection failed with SQLState {sqlstate}: {ex}")
        except Exception as e:
            log_error(f"An unexpected error occurred during connect: {e}", source=SOURCE_CONTEXT)
            raise ConnectionError(f"An unexpected error occurred during connect: {e}")

    def disconnect(self) -> None:
        """
        Closes the connection to the database.
        """
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None

    def is_connected(self) -> bool:
        """
        Checks if a connection to the database is currently active.
        pyodbc connections don't have a simple is_connected method.
        We'll infer based on the presence of the connection object
        and potentially by trying a simple query. For now, just check object existence.
        A more robust check would be to execute 'SELECT 1'.
        """
        if self.connection and self.cursor:
            try:
                self.cursor.execute("SELECT 1")
                return True
            except pyodbc.Error:
                return False
        return False

    # --- Helper methods for query construction and execution ---

    def _map_to_sql_cols(self, data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """Maps generic keys in data to SQL column names."""
        return {mapping[key]: value for key, value in data.items() if key in mapping}

    def _map_from_sql_cols(self, data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """Maps SQL column names in data to generic keys."""
        return {mapping[key]: value for key, value in data.items() if key in mapping}

    def _execute_query(self, query: str, params: Tuple = (), fetch_one: bool = False, fetch_all: bool = False, commit: bool = False) -> Any:
        """Protected method to execute queries using sqlqueriesExe.querie_exe."""
        if not self.is_connected() or not self.connection or not self.cursor:
            raise ConnectionError("Not connected to the database.")
        
        """Protected method to execute queries using the internal cursor."""
        if not self.is_connected() or not self.connection or not self.cursor:
            log_error("Not connected to the database. Cannot execute query.", source=SOURCE_CONTEXT)
            raise ConnectionError("Not connected to the database.")
        
        try:
            log_info(f"Executing query: {query} with params: {params}", source=SOURCE_CONTEXT)
            self.cursor.execute(query, params)

            if commit:
                self.connection.commit()
                log_info("Query committed.", source=SOURCE_CONTEXT)
                return None # No data to return for commit operations typically

            if fetch_one:
                row = self.cursor.fetchone()
                if row:
                    # Get column names from cursor.description
                    columns = [column[0] for column in self.cursor.description]
                    return dict(zip(columns, row))
                return None
            elif fetch_all:
                rows = self.cursor.fetchall()
                if rows:
                    columns = [column[0] for column in self.cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
                return [] # Return empty list if no rows
            
            return None # Default if no fetch mode specified and not a commit operation

        except pyodbc.Error as ex:
            sqlstate = ex.args[0]
            error_message = str(ex)
            log_error(f"SQL Error ({sqlstate}) executing query: {query} with params {params}. Error: {error_message}", source=SOURCE_CONTEXT)
            # Optionally rollback on error, though not strictly necessary for SELECTs
            # if self.connection: self.connection.rollback()
            raise # Re-raise the exception to be handled by the caller or a global error handler
        except Exception as e:
            log_error(f"Unexpected error executing query: {query} with params {params}. Error: {e}", source=SOURCE_CONTEXT)
            raise


    # --- Abstract method implementations ---

    def check_result_exists(self, patient_id: str) -> bool:
        """
        Checks if a test result exists for a given patient using RESULT_EXIST_SQL schema.
        """
        query = f"SELECT TOP 1 {self.result_exist_patient_id_col} FROM {self.result_exist_table_name} WHERE {self.result_exist_condition_pid_col} = ?"
        # Note: RESULT_EXIST_SQL points to 'cbc' table. This implies "result" means a CBC result.
        # If it needs to check other tables, this logic would need to be broader.
        result = self._execute_query(query, params=(patient_id,), fetch_one=True)
        return result is not None

    def save_cbc_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None:
        """Saves a Complete Blood Count (CBC) test result for a patient."""
        if not self.cbc_generic_to_sql_map:
            log_error("CBC generic_to_sql_map is not populated. Cannot save CBC result.", source=SOURCE_CONTEXT)
            # Or raise ConfigurationError("CBC maps not populated")
            return

        # Prepare data for insertion: map generic keys to SQL columns
        sql_insert_data = {}
        for generic_key, value in result_data.items():
            sql_col = self.cbc_generic_to_sql_map.get(generic_key.upper()) # Ensure generic keys are consistently cased
            if sql_col:
                sql_insert_data[sql_col] = value
            else:
                log_warning(f"Generic key '{generic_key}' not found in CBC map. Skipping for save.", source=SOURCE_CONTEXT)
        
        # Add patient_id and request_date, using their SQL column names
        sql_insert_data[self.cbc_sql_patient_id_col] = patient_id
        sql_insert_data[self.cbc_sql_request_date_col] = request_date
        
        if not sql_insert_data:
            log_error("No valid CBC data to save after mapping.", source=SOURCE_CONTEXT)
            return

        columns = ', '.join(sql_insert_data.keys())
        placeholders = ', '.join(['?'] * len(sql_insert_data))
        query = f"INSERT INTO {self.cbc_table_name} ({columns}) VALUES ({placeholders})"
        params = tuple(sql_insert_data.values())
        
        self._execute_query(query, params=params, commit=True)
        log_info(f"CBC result for patient ID {patient_id} saved.", source=SOURCE_CONTEXT)


    def update_cbc_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None:
        """Updates an existing Complete Blood Count (CBC) test result for a patient."""
        if not self.cbc_generic_to_sql_map:
            log_error("CBC generic_to_sql_map is not populated. Cannot update CBC result.", source=SOURCE_CONTEXT)
            return

        sql_update_data = {}
        for generic_key, value in result_data.items():
            sql_col = self.cbc_generic_to_sql_map.get(generic_key.upper())
            if sql_col and sql_col not in [self.cbc_sql_patient_id_col, self.cbc_sql_request_date_col]: # Don't update PK/UK via SET
                sql_update_data[sql_col] = value
            elif not sql_col:
                 log_warning(f"Generic key '{generic_key}' not found in CBC map. Skipping for update.", source=SOURCE_CONTEXT)

        if not sql_update_data: # No fields to update
            log_warning(f"No fields to update for CBC result for patient ID {patient_id}, request date {request_date}.", source=SOURCE_CONTEXT)
            return

        set_clause = ', '.join([f"{col} = ?" for col in sql_update_data.keys()])
        # Condition uses PATIENT_ID and REQ_DATE from the CBC table definition
        query = f"UPDATE {self.cbc_table_name} SET {set_clause} WHERE {self.cbc_sql_patient_id_col} = ? AND {self.cbc_sql_request_date_col} = ?"
        
        params = tuple(sql_update_data.values()) + (patient_id, request_date)
        self._execute_query(query, params=params, commit=True)
        log_info(f"CBC result for patient ID {patient_id}, request date {request_date} updated.", source=SOURCE_CONTEXT)


    def save_hgb_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None:
        """Saves a Hemoglobin (HGB) test result for a patient."""
        if not self.hgb_generic_to_sql_map:
            log_error("HGB generic_to_sql_map is not populated. Cannot save HGB result.", source=SOURCE_CONTEXT)
            return

        sql_insert_data = {}
        for generic_key, value in result_data.items():
            sql_col = self.hgb_generic_to_sql_map.get(generic_key.upper())
            if sql_col:
                sql_insert_data[sql_col] = value
            else:
                log_warning(f"Generic key '{generic_key}' not found in HGB map. Skipping for save.", source=SOURCE_CONTEXT)

        sql_insert_data[self.hgb_sql_patient_id_col] = patient_id
        sql_insert_data[self.hgb_sql_request_date_col] = request_date

        if not sql_insert_data:
            log_error("No valid HGB data to save after mapping.", source=SOURCE_CONTEXT)
            return

        columns = ', '.join(sql_insert_data.keys())
        placeholders = ', '.join(['?'] * len(sql_insert_data))
        query = f"INSERT INTO {self.hgb_table_name} ({columns}) VALUES ({placeholders})" # Note: hgb_table_name is likely same as cbc_table_name
        params = tuple(sql_insert_data.values())

        self._execute_query(query, params=params, commit=True)
        log_info(f"HGB result for patient ID {patient_id} saved.", source=SOURCE_CONTEXT)


    def update_hgb_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None:
        """Updates an existing Hemoglobin (HGB) test result for a patient."""
        if not self.hgb_generic_to_sql_map:
            log_error("HGB generic_to_sql_map is not populated. Cannot update HGB result.", source=SOURCE_CONTEXT)
            return
        
        sql_update_data = {}
        for generic_key, value in result_data.items():
            sql_col = self.hgb_generic_to_sql_map.get(generic_key.upper())
            if sql_col and sql_col not in [self.hgb_sql_patient_id_col, self.hgb_sql_request_date_col]:
                sql_update_data[sql_col] = value
            elif not sql_col:
                log_warning(f"Generic key '{generic_key}' not found in HGB map. Skipping for update.", source=SOURCE_CONTEXT)

        if not sql_update_data:
            log_warning(f"No fields to update for HGB result for patient ID {patient_id}, request date {request_date}.", source=SOURCE_CONTEXT)
            return
            
        set_clause = ', '.join([f"{col} = ?" for col in sql_update_data.keys()])
        query = f"UPDATE {self.hgb_table_name} SET {set_clause} WHERE {self.hgb_sql_patient_id_col} = ? AND {self.hgb_sql_request_date_col} = ?"
        
        params = tuple(sql_update_data.values()) + (patient_id, request_date)
        self._execute_query(query, params=params, commit=True)
        log_info(f"HGB result for patient ID {patient_id}, request date {request_date} updated.", source=SOURCE_CONTEXT)


    def get_patient_info(self, patient_id: str) -> Union[Dict[str, Any], None]:
        """Retrieves patient information using PATIENT_INFO_SQL schema."""
        # Columns to select are the values in patient_info_sql_column_definitions
        select_sql_cols_str = ', '.join(self.patient_info_sql_column_definitions.values())
        # Condition column for patient_id
        condition_col = self.patient_info_condition_pid_col
        
        query = f"SELECT {select_sql_cols_str} FROM {self.patient_info_table_name} WHERE {condition_col} = ?"
        
        row_dict_sql_keys = self._execute_query(query, params=(patient_id,), fetch_one=True) # Returns dict with SQL keys
        
        if row_dict_sql_keys:
            # Map SQL column names back to generic keys
            generic_info = {
                self.patient_info_sql_to_generic_map.get(sql_col, sql_col.strip("[]")): value
                for sql_col, value in row_dict_sql_keys.items()
                if sql_col in self.patient_info_sql_to_generic_map # Ensure only mapped columns are returned
            }
            return generic_info
        return None


    def get_patient_test_request(self, patient_id: str) -> Union[Dict[str, Any], None]:
        """Retrieves test request information for a patient using PATIENT_TEST_SQL."""
        select_sql_cols_str = ', '.join(self.patient_test_sql_column_definitions.values())
        condition_col = self.patient_test_condition_pid_col

        query = f"SELECT {select_sql_cols_str} FROM {self.patient_test_table_name} WHERE {condition_col} = ?"
        # This might return multiple rows if a patient has multiple test requests.
        # The adapter interface implies one Dict or None. Assuming TOP 1 or specific logic needed.
        # For now, let's fetch the first one found. Add TOP 1 for MSSQL.
        query = f"SELECT TOP 1 {select_sql_cols_str} FROM {self.patient_test_table_name} WHERE {condition_col} = ?"

        row_dict_sql_keys = self._execute_query(query, params=(patient_id,), fetch_one=True)
        
        if row_dict_sql_keys:
            generic_data = {
                self.patient_test_sql_to_generic_map.get(sql_col, sql_col.strip("[]")): value
                for sql_col, value in row_dict_sql_keys.items()
                if sql_col in self.patient_test_sql_to_generic_map
            }
            return generic_data
        return None


    def execute_procedure(self, procedure_name: str, params: Dict[str, Any]) -> Union[List[Dict[str, Any]], None]:
        """
        Executes a stored procedure.
        Uses procedure definitions from sqldbdictionary to map generic param names to expected order.
        """
        proc_details = None
        ordered_param_names = []

        if procedure_name == self.patient_search_proc_name:
            proc_details = sqldbdictionary.PATIENT_SEARCH_SQL
            ordered_param_names = self.patient_search_proc_params
        elif procedure_name == self.patient_cbc_result_proc_name:
            proc_details = sqldbdictionary.PATIENT_CBC_RESULT_SQL
            ordered_param_names = self.patient_cbc_result_proc_params
        else:
            log_error(f"Procedure '{procedure_name}' is not defined in sqldbdictionary.", source=SOURCE_CONTEXT)
            raise ValueError(f"Procedure '{procedure_name}' is not defined.")

        # Prepare parameters in the order specified by sqldbdictionary's PARAMETERS list
        param_values_list: List[Any] = []
        for p_name in ordered_param_names:
            if p_name not in params:
                # Procedures might have optional params with defaults in DB, or this is an error.
                # For now, assume all defined params in dict must be provided if they are in `params` input.
                # If a param from `ordered_param_names` is not in `params` input, pass None.
                log_warning(f"Parameter '{p_name}' for procedure '{procedure_name}' not found in input params. Using None.", source=SOURCE_CONTEXT)
                param_values_list.append(None) 
            else:
                param_values_list.append(params[p_name])
        
        param_values_tuple = tuple(param_values_list)
        
        placeholders = ', '.join(['?'] * len(param_values_tuple))
        # Using ODBC standard call syntax
        query = f"{{CALL {procedure_name} ({placeholders})}}"
        
        # Procedures might return results and might also modify data (though less common for SELECT-like procs)
        # Assuming commit=False for procedures that are expected to return data primarily.
        # If a procedure modifies data and does not return a result set, commit should be True.
        # This needs to be configurable or decided based on procedure type.
        # For GetPatientInfo and GetPatientCBCResult, they likely return data.
        
        results = self._execute_query(query, params=param_values_tuple, fetch_all=True, commit=False)
        
        # _execute_query already returns list of dicts if fetch_all=True and rows exist.
        # No further mapping of keys is assumed here, as procedure result columns are not predefined
        # in the same way as table columns in sqldbdictionary for generic mapping.
        # If procedures have fixed output columns that need mapping, that would be an extension.
        return results if results else [] # Return empty list if None/empty from _execute_query
   

    # Methods like _map_to_sql_cols and _map_from_sql_cols can be removed if direct mapping
    # in each method is preferred and self.xxx_generic_to_sql_map is used.
    # The _dynamic_populate methods are now specific and called from __init__.
    # Removed old _dynamic_populate_... methods that were placeholders.
    # The new _dynamic_populate_... methods are called from __init__ and are more specific.
    # The previous _map_to_sql_cols and _map_from_sql_cols were too generic and might
    # not fit all scenarios without passing map names. Better to be explicit in each method.
    # Removing placeholder methods for populating maps from the old version.
    # The actual population logic is now in _dynamic_populate_cbc_map_from_sqldict and _dynamic_populate_hgb_map_from_sqldict.

    # Ensure all abstract methods from DatabaseAdapter are implemented.
    # connect, disconnect, is_connected, check_result_exists,
    # save_cbc_result, update_cbc_result, save_hgb_result, update_hgb_result,
    # get_patient_info, get_patient_test_request, execute_procedure.
    # All seem to be defined.
