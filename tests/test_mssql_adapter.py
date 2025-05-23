import unittest
from unittest.mock import patch, MagicMock, call
import pyodbc # For ConnectionError and other pyodbc specific exceptions if needed

# Import the class to be tested
from database.mssql_adapter import MssqlAdapter

# Mocked versions of sqldbdictionary structures for test stability
# These should reflect the structure the adapter expects.
MOCK_RESULT_EXIST_SQL = {
    "TABLE_NAME": "[cbc]",
    "COLUMN_NAME": {"PATIENT_ID": "[patientid]"},
    "CONDITION": {"PATIENT_ID": "[patientid]"},
}

MOCK_CBC_RESULT_SQL = {
    "TABLE_NAME": "[cbc]",
    "COLUMN_NAME": {
        "PATIENT_ID": "[patientid]",
        "REQ_DATE": "[requestdate]",
        "HGB": "[hgb]",
        "RBC": "[rbc]",
        "WBC": "[wbc]",
    },
}

MOCK_HGB_RESULT_SQL = {
    "TABLE_NAME": "[cbc]", # Assuming HGB also goes to cbc table as per actual dict
    "COLUMN_NAME": {
        "PATIENT_ID": "[patientid]",
        "REQ_DATE": "[requestdate]",
        "HGB": "[hgb]",
    },
}

MOCK_PATIENT_INFO_SQL = {
    "TABLE_NAME": "[patientinfo]",
    "COLUMN_NAME": {
        "NAME": "[patientnamear]",
        "SEX": "[patientsex]",
        "AGE": "[patientage]",
        # REQ_DATE is often in PATIENT_INFO_SQL in real scenarios, adding for completeness
        "REQ_DATE": "[requestdate]", 
    },
    "CONDITION": {"PATIENT_ID": "[patientid]"},
}

MOCK_PATIENT_TEST_SQL = {
    "TABLE_NAME": "[patienttest]",
    "COLUMN_NAME": {"TEST_CODE": "[testcode]", "RESULT_STATE": "[resultfinsh]"},
    "CONDITION": {"PATIENT_ID": "[patientid]"},
}

MOCK_PATIENT_SEARCH_SQL = {
    "PROCEDURE_NAME": "GetPatientInfo",
    "PARAMETERS": ["PATIENT_ID", "PATIENT_NAME", "START_DATE", "END_DATE", "RESULT_FINISHED"],
}

MOCK_PATIENT_CBC_RESULT_SQL = {
    "PROCEDURE_NAME": "GetPatientCBCResult",
    "PARAMETERS": ["PATIENT_ID"],
}


class TestMssqlAdapter(unittest.TestCase):

    @patch('database.mssql_adapter.sqldbdictionary.RESULT_EXIST_SQL', MOCK_RESULT_EXIST_SQL)
    @patch('database.mssql_adapter.sqldbdictionary.CBC_RESULT_SQL', MOCK_CBC_RESULT_SQL)
    @patch('database.mssql_adapter.sqldbdictionary.HGB_RESULT_SQL', MOCK_HGB_RESULT_SQL)
    @patch('database.mssql_adapter.sqldbdictionary.PATIENT_INFO_SQL', MOCK_PATIENT_INFO_SQL)
    @patch('database.mssql_adapter.sqldbdictionary.PATIENT_TEST_SQL', MOCK_PATIENT_TEST_SQL)
    @patch('database.mssql_adapter.sqldbdictionary.PATIENT_SEARCH_SQL', MOCK_PATIENT_SEARCH_SQL)
    @patch('database.mssql_adapter.sqldbdictionary.PATIENT_CBC_RESULT_SQL', MOCK_PATIENT_CBC_RESULT_SQL)
    @patch('database.mssql_adapter.get_db_connection')
    def setUp(self, mock_get_db_connection):
        # Configure the mock connection and cursor
        self.mock_connection = MagicMock(spec=pyodbc.Connection)
        self.mock_cursor = MagicMock(spec=pyodbc.Cursor)
        self.mock_connection.cursor.return_value = self.mock_cursor
        mock_get_db_connection.return_value = self.mock_connection

        # Instantiate the adapter
        # Patch the _dynamic_populate methods as they depend on the full sqldbdictionary structure
        # which we are partially mocking. The core logic of these methods (map creation)
        # will be implicitly tested by how other methods use the maps.
        # Alternatively, we can let them run if our mock sqldbdictionary is complete enough for them.
        # For now, let's mock them to avoid issues if MOCK_..._SQL dicts are not 100% complete for map generation.
        with patch.object(MssqlAdapter, '_dynamic_populate_cbc_map_from_sqldict', return_value=None), \
             patch.object(MssqlAdapter, '_dynamic_populate_hgb_map_from_sqldict', return_value=None):
            self.adapter = MssqlAdapter()
        
        # Manually populate maps for testing based on our MOCK_..._SQL structures
        # This ensures test methods have the maps they need, consistent with mocked schemas.
        self.adapter.cbc_generic_to_sql_map = {k: v for k, v in MOCK_CBC_RESULT_SQL["COLUMN_NAME"].items()}
        self.adapter.cbc_sql_to_generic_map = {v: k for k, v in self.adapter.cbc_generic_to_sql_map.items()}
        self.adapter.hgb_generic_to_sql_map = {k: v for k, v in MOCK_HGB_RESULT_SQL["COLUMN_NAME"].items()}
        self.adapter.hgb_sql_to_generic_map = {v: k for k, v in self.adapter.hgb_generic_to_sql_map.items()}

        self.adapter.patient_info_sql_to_generic_map = {
            sql_col: generic_key for generic_key, sql_col in MOCK_PATIENT_INFO_SQL["COLUMN_NAME"].items()
        }
        self.adapter.patient_test_sql_to_generic_map = {
            sql_col: generic_key for generic_key, sql_col in MOCK_PATIENT_TEST_SQL["COLUMN_NAME"].items()
        }


    @patch('database.mssql_adapter.get_db_connection') # Re-patch for this specific test's assertion
    def test_connect_disconnect(self, mock_get_db_connection_local):
        # Configure the mock connection and cursor for this specific test
        mock_conn = MagicMock(spec=pyodbc.Connection)
        mock_curs = MagicMock(spec=pyodbc.Cursor)
        mock_conn.cursor.return_value = mock_curs
        mock_get_db_connection_local.return_value = mock_conn

        adapter_instance = MssqlAdapter() # Create a new instance for this test

        # Test connect
        with patch.object(adapter_instance, '_dynamic_populate_cbc_map_from_sqldict') as mock_populate_cbc, \
             patch.object(adapter_instance, '_dynamic_populate_hgb_map_from_sqldict') as mock_populate_hgb:
            adapter_instance.connect({})
        
        mock_get_db_connection_local.assert_called_once()
        self.assertIsNotNone(adapter_instance.connection)
        self.assertIsNotNone(adapter_instance.cursor)
        mock_conn.cursor.assert_called_once()
        # _dynamic_populate methods are called in __init__, but connect ensures cursor exists before they'd be useful.
        # The original code called them in connect *after* cursor creation.
        # With them called in __init__ now, this specific check in connect is less direct.
        # We've already mocked them out during the main setUp.
        # For this test, we ensure connect() did its job of setting up connection/cursor.

        # Test disconnect
        adapter_instance.disconnect()
        mock_curs.close.assert_called_once()
        mock_conn.close.assert_called_once()
        self.assertIsNone(adapter_instance.cursor)
        self.assertIsNone(adapter_instance.connection)

    def test_is_connected(self):
        # 1. Test when not connected (before connect is called or after disconnect)
        self.adapter.connection = None # Ensure disconnected state
        self.adapter.cursor = None
        self.assertFalse(self.adapter.is_connected())

        # 2. Test when connected and "SELECT 1" succeeds
        self.adapter.connection = self.mock_connection
        self.adapter.cursor = self.mock_cursor
        self.mock_cursor.execute.return_value = None # SELECT 1 doesn't return rows via fetch
        self.assertTrue(self.adapter.is_connected())
        self.mock_cursor.execute.assert_called_with("SELECT 1")

        # 3. Test when connected but "SELECT 1" fails (e.g., connection dropped)
        self.mock_cursor.execute.side_effect = pyodbc.Error("Connection lost")
        self.assertFalse(self.adapter.is_connected())
    
    def test_check_result_exists_true(self):
        self.adapter.connect({}) # Ensure connection and cursor are set
        self.mock_cursor.fetchone.return_value = ( "some_patient_id", ) # Simulate data returned
        
        exists = self.adapter.check_result_exists("PAT123")
        
        self.assertTrue(exists)
        expected_query = f"SELECT TOP 1 {MOCK_RESULT_EXIST_SQL['COLUMN_NAME']['PATIENT_ID']} FROM {MOCK_RESULT_EXIST_SQL['TABLE_NAME']} WHERE {MOCK_RESULT_EXIST_SQL['CONDITION']['PATIENT_ID']} = ?"
        self.mock_cursor.execute.assert_called_with(expected_query, ("PAT123",))

    def test_check_result_exists_false(self):
        self.adapter.connect({})
        self.mock_cursor.fetchone.return_value = None # Simulate no data returned
        
        exists = self.adapter.check_result_exists("PAT456")
        
        self.assertFalse(exists)
        expected_query = f"SELECT TOP 1 {MOCK_RESULT_EXIST_SQL['COLUMN_NAME']['PATIENT_ID']} FROM {MOCK_RESULT_EXIST_SQL['TABLE_NAME']} WHERE {MOCK_RESULT_EXIST_SQL['CONDITION']['PATIENT_ID']} = ?"
        self.mock_cursor.execute.assert_called_with(expected_query, ("PAT456",))

    def test_save_cbc_result(self):
        self.adapter.connect({})
        patient_id = "PID001"
        request_date = "2023-01-01 10:00:00"
        # Generic keys must match those in MOCK_CBC_RESULT_SQL["COLUMN_NAME"]
        result_data = {"HGB": 12.5, "RBC": 4.5, "WBC": 7.0} 

        self.adapter.save_cbc_result(patient_id, result_data, request_date)

        # Expected SQL columns from MOCK_CBC_RESULT_SQL["COLUMN_NAME"]
        # Order matters for params, so construct query and params carefully based on dict iteration order (Python 3.7+)
        # or a fixed order if the adapter sorts them. The adapter code iterates sql_insert_data.keys().
        
        # Build expected sql_insert_data to determine order for assertion
        expected_sql_insert_data = {
            MOCK_CBC_RESULT_SQL["COLUMN_NAME"]["HGB"]: 12.5,
            MOCK_CBC_RESULT_SQL["COLUMN_NAME"]["RBC"]: 4.5,
            MOCK_CBC_RESULT_SQL["COLUMN_NAME"]["WBC"]: 7.0,
            MOCK_CBC_RESULT_SQL["COLUMN_NAME"]["PATIENT_ID"]: patient_id,
            MOCK_CBC_RESULT_SQL["COLUMN_NAME"]["REQ_DATE"]: request_date,
        }
        
        expected_columns_str = ', '.join(expected_sql_insert_data.keys())
        expected_placeholders_str = ', '.join(['?'] * len(expected_sql_insert_data))
        expected_query = f"INSERT INTO {MOCK_CBC_RESULT_SQL['TABLE_NAME']} ({expected_columns_str}) VALUES ({expected_placeholders_str})"
        expected_params = tuple(expected_sql_insert_data.values())

        self.mock_cursor.execute.assert_called_with(expected_query, expected_params)
        self.mock_connection.commit.assert_called_once()

    def test_save_hgb_result(self):
        self.adapter.connect({})
        patient_id = "PID002"
        request_date = "2023-01-02 11:00:00"
        result_data = {"HGB": 10.1}

        self.adapter.save_hgb_result(patient_id, result_data, request_date)

        expected_sql_insert_data = {
            MOCK_HGB_RESULT_SQL["COLUMN_NAME"]["HGB"]: 10.1,
            MOCK_HGB_RESULT_SQL["COLUMN_NAME"]["PATIENT_ID"]: patient_id,
            MOCK_HGB_RESULT_SQL["COLUMN_NAME"]["REQ_DATE"]: request_date,
        }
        expected_columns_str = ', '.join(expected_sql_insert_data.keys())
        expected_placeholders_str = ', '.join(['?'] * len(expected_sql_insert_data))
        expected_query = f"INSERT INTO {MOCK_HGB_RESULT_SQL['TABLE_NAME']} ({expected_columns_str}) VALUES ({expected_placeholders_str})"
        expected_params = tuple(expected_sql_insert_data.values())

        self.mock_cursor.execute.assert_called_with(expected_query, expected_params)
        self.mock_connection.commit.assert_called_once()


    def test_update_cbc_result(self):
        self.adapter.connect({})
        patient_id = "PID003"
        request_date = "2023-01-03 12:00:00"
        result_data = {"HGB": 13.0, "WBC": 8.0} # RBC not updated

        self.adapter.update_cbc_result(patient_id, result_data, request_date)

        # Build expected sql_update_data
        expected_sql_update_data = {
            MOCK_CBC_RESULT_SQL["COLUMN_NAME"]["HGB"]: 13.0,
            MOCK_CBC_RESULT_SQL["COLUMN_NAME"]["WBC"]: 8.0,
        }
        set_clause = ', '.join([f"{col} = ?" for col in expected_sql_update_data.keys()])
        expected_query = f"UPDATE {MOCK_CBC_RESULT_SQL['TABLE_NAME']} SET {set_clause} WHERE {MOCK_CBC_RESULT_SQL['COLUMN_NAME']['PATIENT_ID']} = ? AND {MOCK_CBC_RESULT_SQL['COLUMN_NAME']['REQ_DATE']} = ?"
        expected_params = tuple(expected_sql_update_data.values()) + (patient_id, request_date)

        self.mock_cursor.execute.assert_called_with(expected_query, expected_params)
        self.mock_connection.commit.assert_called_once()


    def test_get_patient_info(self):
        self.adapter.connect({})
        patient_id = "PID004"
        
        # Define what the cursor description and fetchone should return
        # Column names must match values in MOCK_PATIENT_INFO_SQL["COLUMN_NAME"]
        self.mock_cursor.description = [
            (MOCK_PATIENT_INFO_SQL["COLUMN_NAME"]["NAME"],),
            (MOCK_PATIENT_INFO_SQL["COLUMN_NAME"]["SEX"],),
            (MOCK_PATIENT_INFO_SQL["COLUMN_NAME"]["AGE"],),
            (MOCK_PATIENT_INFO_SQL["COLUMN_NAME"]["REQ_DATE"],),
        ]
        mock_row_tuple = ("John Doe", "M", 30, "2023-01-04 10:00:00")
        self.mock_cursor.fetchone.return_value = mock_row_tuple

        retrieved_info = self.adapter.get_patient_info(patient_id)

        expected_select_cols = ', '.join(MOCK_PATIENT_INFO_SQL["COLUMN_NAME"].values())
        expected_query = f"SELECT {expected_select_cols} FROM {MOCK_PATIENT_INFO_SQL['TABLE_NAME']} WHERE {MOCK_PATIENT_INFO_SQL['CONDITION']['PATIENT_ID']} = ?"
        self.mock_cursor.execute.assert_called_with(expected_query, (patient_id,))
        
        # Expected generic keys are keys from MOCK_PATIENT_INFO_SQL["COLUMN_NAME"]
        expected_info = {
            "NAME": "John Doe",
            "SEX": "M",
            "AGE": 30,
            "REQ_DATE": "2023-01-04 10:00:00"
        }
        self.assertEqual(retrieved_info, expected_info)

    def test_get_patient_test_request(self):
        self.adapter.connect({})
        patient_id = "PID005"

        self.mock_cursor.description = [
            (MOCK_PATIENT_TEST_SQL["COLUMN_NAME"]["TEST_CODE"],),
            (MOCK_PATIENT_TEST_SQL["COLUMN_NAME"]["RESULT_STATE"],),
        ]
        mock_row_tuple = ("CBC", "Pending")
        self.mock_cursor.fetchone.return_value = mock_row_tuple

        retrieved_request = self.adapter.get_patient_test_request(patient_id)

        expected_select_cols = ', '.join(MOCK_PATIENT_TEST_SQL["COLUMN_NAME"].values())
        expected_query = f"SELECT TOP 1 {expected_select_cols} FROM {MOCK_PATIENT_TEST_SQL['TABLE_NAME']} WHERE {MOCK_PATIENT_TEST_SQL['CONDITION']['PATIENT_ID']} = ?"
        self.mock_cursor.execute.assert_called_with(expected_query, (patient_id,))

        expected_request = {
            "TEST_CODE": "CBC",
            "RESULT_STATE": "Pending"
        }
        self.assertEqual(retrieved_request, expected_request)

    def test_execute_procedure_patient_search_returns_data(self):
        self.adapter.connect({})
        procedure_name = MOCK_PATIENT_SEARCH_SQL["PROCEDURE_NAME"]
        # Params keys must match MOCK_PATIENT_SEARCH_SQL["PARAMETERS"]
        params = {
            "PATIENT_ID": "PID006", 
            "PATIENT_NAME": "Jane", 
            "START_DATE": "2023-01-01", 
            "END_DATE": "2023-01-31", 
            "RESULT_FINISHED": True
        }

        # Expected ordered values based on MOCK_PATIENT_SEARCH_SQL["PARAMETERS"]
        expected_param_values = ("PID006", "Jane", "2023-01-01", "2023-01-31", True)
        
        self.mock_cursor.description = [("PatientID",), ("PatientName",), ("TestDate",)]
        self.mock_cursor.fetchall.return_value = [("PID006", "Jane Doe", "2023-01-15")]

        results = self.adapter.execute_procedure(procedure_name, params)

        placeholders = ', '.join(['?'] * len(expected_param_values))
        expected_query = f"{{CALL {procedure_name} ({placeholders})}}"
        self.mock_cursor.execute.assert_called_with(expected_query, expected_param_values)
        
        expected_results = [{"PatientID": "PID006", "PatientName": "Jane Doe", "TestDate": "2023-01-15"}]
        self.assertEqual(results, expected_results)
        self.mock_connection.commit.assert_not_called() # commit=False for data retrieval procs

    def test_execute_procedure_patient_cbc_result_no_data(self):
        self.adapter.connect({})
        procedure_name = MOCK_PATIENT_CBC_RESULT_SQL["PROCEDURE_NAME"]
        params = {"PATIENT_ID": "PID007"}
        expected_param_values = ("PID007",) # Based on MOCK_PATIENT_CBC_RESULT_SQL["PARAMETERS"]

        self.mock_cursor.fetchall.return_value = [] # Procedure returns no data

        results = self.adapter.execute_procedure(procedure_name, params)

        placeholders = ', '.join(['?'] * len(expected_param_values))
        expected_query = f"{{CALL {procedure_name} ({placeholders})}}"
        self.mock_cursor.execute.assert_called_with(expected_query, expected_param_values)
        
        self.assertEqual(results, [])


if __name__ == '__main__':
    unittest.main()
