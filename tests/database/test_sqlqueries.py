import pytest
from database.sqlqueriesExe import querie_exe
from database.sqlqueries import data_insert_for, data_update_for, data_select_for, data_delete_for, exec_procedure_for, exec_procedure_no_return
from database.sqlconnection import get_db_connection

def test_querie_exe_select(mock_db_connection, mock_logger):
    conn, cursor = mock_db_connection

    # Mock return data
    cursor.fetchall.return_value = [(1, "Test")]
    # Mock description (needed for result mapping if we were doing it dynamically, but here we manually zip)

    data = ("SELECT * FROM table", (), ("ID", "Name"))
    result = querie_exe(data)

    assert result == {"ID": 1, "Name": "Test"}
    cursor.execute.assert_called_with("SELECT * FROM table", ())

def test_querie_exe_select_no_results(mock_db_connection, mock_logger):
    conn, cursor = mock_db_connection
    cursor.fetchall.return_value = []

    data = ("SELECT * FROM table", (), ("ID", "Name"))
    result = querie_exe(data)

    assert result is None

def test_querie_exe_insert(mock_db_connection, mock_logger):
    conn, cursor = mock_db_connection

    data = ("INSERT INTO table VALUES (?)", (1,))
    result = querie_exe(data)

    assert result is None
    conn.commit.assert_called_once()

def test_querie_exe_exec_with_results(mock_db_connection, mock_logger):
    conn, cursor = mock_db_connection
    cursor.fetchall.return_value = [(1, "Value")]
    cursor.description = [("ID", None, None, None, None, None, None), ("Name", None, None, None, None, None, None)]

    data = ("EXEC MyProc", ())
    result = querie_exe(data, expect_results=True)

    assert len(result) == 1
    assert result[0]["ID"] == 1
    assert result[0]["Name"] == "Value"

def test_data_insert_for(mocker, mock_logger):
    # Mock update_hl7_dictionary
    mocker.patch("database.sqlqueries.update_hl7_dictionary", return_value={
        "COLUMN_NAME": {"Col1": "Val1"}
    })

    mock_querie_exe = mocker.patch("database.sqlqueries.querie_exe")

    db_schema = {
        "TABLE_NAME": "TestTable",
        "COLUMN_NAME": {"Col1": "Col1_DB"}
    }
    hl7_dict = {"COLUMN_NAME": {}}
    hl7_msg = mocker.MagicMock()

    data_insert_for(db_schema, hl7_dict, hl7_msg)

    args, _ = mock_querie_exe.call_args
    sql, values = args[0]

    assert "INSERT INTO [dbo].TestTable" in sql
    assert "Col1_DB" in sql
    assert values == ("Val1",)

def test_data_update_for(mocker, mock_logger):
    mocker.patch("database.sqlqueries.update_hl7_dictionary", return_value={
        "COLUMN_NAME": {"Col1": "Val1"},
        "CONDITION": {"Cond1": "CondVal1"}
    })

    mock_querie_exe = mocker.patch("database.sqlqueries.querie_exe")

    db_schema = {
        "TABLE_NAME": "TestTable",
        "COLUMN_NAME": {"Col1": "Col1_DB"},
        "CONDITION": {"Cond1": "Cond1_DB"}
    }
    hl7_dict = {"COLUMN_NAME": {}, "CONDITION": {}}
    hl7_msg = mocker.MagicMock()

    data_update_for(db_schema, hl7_dict, hl7_msg)

    args, _ = mock_querie_exe.call_args
    sql, values = args[0]

    assert "UPDATE [dbo].TestTable" in sql
    assert "SET Col1_DB = ?" in sql
    assert "WHERE Cond1_DB = ?" in sql
    assert values == ("Val1", "CondVal1")

def test_data_select_for(mocker, mock_logger):
    mocker.patch("database.sqlqueries.update_hl7_dictionary", return_value={
        "CONDITION": {"Cond1": "CondVal1"}
    })

    mock_querie_exe = mocker.patch("database.sqlqueries.querie_exe", return_value={"Col1": "Result"})

    db_schema = {
        "TABLE_NAME": "TestTable",
        "COLUMN_NAME": {"Col1": "Col1_DB"},
        "CONDITION": {"Cond1": "Cond1_DB"}
    }
    hl7_dict = {"CONDITION": {}}
    hl7_msg = mocker.MagicMock()

    result = data_select_for(db_schema, hl7_dict, hl7_msg)

    assert result == {"Col1": "Result"}

    args, _ = mock_querie_exe.call_args
    sql, values, selected_vars = args[0]

    assert "SELECT Col1_DB FROM [dbo].TestTable" in sql
    assert values == ("CondVal1",)

def test_exec_procedure_for(mocker, mock_logger):
    mock_querie_exe = mocker.patch("database.sqlqueries.querie_exe", return_value="Result")

    db_schema = {
        "PROCEDURE_NAME": "MyProc",
        "PARAMETERS": ["Param1"]
    }
    values = {"Param1": "Value1"}

    import asyncio
    asyncio.run(exec_procedure_for(db_schema, values))

    args, _ = mock_querie_exe.call_args
    sql, val = args[0]

    assert "EXEC MyProc @Param1 = ?" in sql
    assert val == ("Value1",)

def test_exec_procedure_no_return(mocker, mock_logger):
    mock_querie_exe = mocker.patch("database.sqlqueries.querie_exe")

    db_schema = {
        "PROCEDURE_NAME": "MyProc",
        "PARAMETERS": ["Param1"]
    }
    values = {"Param1": "Value1"}

    import asyncio
    asyncio.run(exec_procedure_no_return(db_schema, values))

    args, kwargs = mock_querie_exe.call_args
    assert kwargs.get('expect_results') is False


def test_data_insert_for_schema_immutability(mocker, mock_logger):
    """
    Verify that executing data_insert_for with missing fields does NOT mutate
    the input db_schema dictionary, allowing subsequent full-field insertions to succeed.
    """
    mock_querie_exe = mocker.patch("database.sqlqueries.querie_exe")

    db_schema = {
        "TABLE_NAME": "TestTable",
        "COLUMN_NAME": {
            "Col1": "Col1_DB",
            "Col2": "Col2_DB",
            "Col3": "Col3_DB"
        }
    }

    # Pass 1: HL7 message with partial data (only Col1)
    mocker.patch("database.sqlqueries.update_hl7_dictionary", return_value={
        "COLUMN_NAME": {"Col1": "Val1"}
    })
    hl7_dict = {"COLUMN_NAME": {}}
    hl7_msg = mocker.MagicMock()

    data_insert_for(db_schema, hl7_dict, hl7_msg)

    # Assert db_schema was NOT modified in-place
    assert len(db_schema["COLUMN_NAME"]) == 3
    assert set(db_schema["COLUMN_NAME"].keys()) == {"Col1", "Col2", "Col3"}

    first_call_sql, first_call_val = mock_querie_exe.call_args_list[0][0][0]
    assert "Col1_DB" in first_call_sql
    assert "Col2_DB" not in first_call_sql
    assert first_call_val == ("Val1",)

    # Pass 2: Subsequent HL7 message with full data (Col1, Col2, Col3)
    mocker.patch("database.sqlqueries.update_hl7_dictionary", return_value={
        "COLUMN_NAME": {"Col1": "Val1", "Col2": "Val2", "Col3": "Val3"}
    })

    data_insert_for(db_schema, hl7_dict, hl7_msg)

    # Verify db_schema still has all columns
    assert len(db_schema["COLUMN_NAME"]) == 3
    assert set(db_schema["COLUMN_NAME"].keys()) == {"Col1", "Col2", "Col3"}

    # Verify second call successfully inserted all 3 fields
    second_call_sql, second_call_val = mock_querie_exe.call_args_list[1][0][0]
    assert "Col1_DB" in second_call_sql
    assert "Col2_DB" in second_call_sql
    assert "Col3_DB" in second_call_sql
    assert second_call_val == ("Val1", "Val2", "Val3")


def test_data_update_for_schema_immutability(mocker, mock_logger):
    """
    Verify that executing data_update_for with missing fields does NOT mutate
    the input db_schema dictionary, preserving all columns for subsequent calls.
    """
    mock_querie_exe = mocker.patch("database.sqlqueries.querie_exe")

    db_schema = {
        "TABLE_NAME": "TestTable",
        "COLUMN_NAME": {
            "Col1": "Col1_DB",
            "Col2": "Col2_DB"
        },
        "CONDITION": {
            "Cond1": "Cond1_DB"
        }
    }

    # Pass 1: Partial update (only Col1)
    mocker.patch("database.sqlqueries.update_hl7_dictionary", return_value={
        "COLUMN_NAME": {"Col1": "Val1"},
        "CONDITION": {"Cond1": "CondVal1"}
    })
    hl7_dict = {"COLUMN_NAME": {}, "CONDITION": {}}
    hl7_msg = mocker.MagicMock()

    data_update_for(db_schema, hl7_dict, hl7_msg)

    # Assert db_schema was NOT modified in-place
    assert len(db_schema["COLUMN_NAME"]) == 2
    assert set(db_schema["COLUMN_NAME"].keys()) == {"Col1", "Col2"}

    # Pass 2: Full update (Col1 and Col2)
    mocker.patch("database.sqlqueries.update_hl7_dictionary", return_value={
        "COLUMN_NAME": {"Col1": "Val1", "Col2": "Val2"},
        "CONDITION": {"Cond1": "CondVal1"}
    })

    data_update_for(db_schema, hl7_dict, hl7_msg)

    # Verify second call updated both columns
    second_call_sql, second_call_val = mock_querie_exe.call_args_list[1][0][0]
    assert "Col1_DB = ?" in second_call_sql
    assert "Col2_DB = ?" in second_call_sql
    assert second_call_val == ("Val1", "Val2", "CondVal1")


def test_data_select_and_delete_none_parameter_binding(mocker, mock_logger):
    """
    Verify that data_select_for and data_delete_for bind missing/None fields as None (SQL NULL),
    preventing literal string 'None' SQL binding regressions. (M-1 fix)
    """
    mock_querie_exe = mocker.patch("database.sqlqueries.querie_exe")

    db_schema = {
        "TABLE_NAME": "Patient",
        "COLUMN_NAME": {"Name": "PatientName"},
        "CONDITION": {"PatientID": "Patient_ID", "SampleID": "Sample_ID"}
    }

    # update_hl7_dictionary returns one None field and one literal "None" field
    mocker.patch("database.sqlqueries.update_hl7_dictionary", return_value={
        "COLUMN_NAME": {"Name": "Doe"},
        "CONDITION": {"PatientID": None, "SampleID": "None"}
    })

    hl7_dict = {"COLUMN_NAME": {}, "CONDITION": {}}
    hl7_msg = mocker.MagicMock()

    # 1. Test data_select_for
    data_select_for(db_schema, hl7_dict, hl7_msg)
    select_data = mock_querie_exe.call_args_list[0][0][0]
    select_sql, select_values, _ = select_data
    assert select_values == (None, None)
    assert "None" not in select_values  # Must be Python None, not str 'None'

    # 2. Test data_delete_for
    data_delete_for(db_schema, hl7_dict, hl7_msg)
    delete_data = mock_querie_exe.call_args_list[1][0][0]
    delete_sql, delete_values = delete_data
    assert delete_values == (None, None)
    assert "None" not in delete_values

