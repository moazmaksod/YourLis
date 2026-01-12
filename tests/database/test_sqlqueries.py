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
