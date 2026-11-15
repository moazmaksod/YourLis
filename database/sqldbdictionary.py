"""
Configure database schema for tables and columns.

Each schema definition is in the following format:
{
    "DB_NAME": "[DB_NAME]",
    "TABLE_NAME": "[TABLE_NAME]",
    "COLUMN_NAME": {
        "ITEM_NAME": "[COLUMN_NAME]",
        "ANOTHER_ITEM_NAME": "[COLUMN_NAME]"
    },
    "CONDITION": {
        "CONDITION_NAME": "[COLUMN_NAME]",
        "ANOTHER_CONDITION_NAME": "[COLUMN_NAME]"
    }
}
"""

from log.logger import log_info

# Define source for logging
SOURCE = "Database"

log_info("Loading database schema definitions...", source=SOURCE)

# Define tables and columns for checking the existence of a patient record
RESULT_EXIST_SQL = {
    "DB_NAME": "[patients]",
    "TABLE_NAME": "[cbc]",
    "COLUMN_NAME": {"PATIENT_ID": "[patientid]"},
    "CONDITION": {"PATIENT_ID": "[patientid]"},
}



# Define tables and columns for CBC results to insert or update
CBC_RESULT_SQL = {
    "DB_NAME": "[patients]",
    "TABLE_NAME": "[cbc]",
    "COLUMN_NAME": {
        "PATIENT_ID": "[patientid]",
        "REQ_DATE": "[requestdate]",
        "HGB": "[hgb]",
        "RBC": "[rbc]",
        "HCT": "[hct]",
        "PLT": "[plt]",
        "HGB%": "[hgbper]",
        "MCV": "[mcv]",
        "MCH": "[mch]",
        "MCHC": "[mchc]",
        "PCT": "[pct]",
        "MPV": "[mpv]",
        "WBC": "[wbc]",
        "NEUTROPHIL": "[neut]",
        "LYMPHOCYTE": "[lymph]",
        "MONOCYTE": "[mono]",
        "EOSINOPHIL": "[eosino]",
        "BASOPHIL": "[baso]",
        "OTHERCELL": "[othercell]",
        "RDW": "[rdw]",
        "PDW": "[pdw]",
        "SEGMENT": "[seg]",
        "BAND": "[bandx]",
        "COMMENT": "[comment]",
        "JUVENILE": "[Juvenile]",
        "MYELOCYTES": "[Myelocytes]",
        "PROMYELOCYTE": "[Promyelocyte]",
        "BLAST": "[Blast]",
        "NRBCWBC": "[NRBCWBC]",
    },
    "CONDITION": {"PATIENT_ID": "[patientid]"},
}

# Define tables and columns for HGB results to insert or update
HGB_RESULT_SQL = {
    "DB_NAME": "[patients]",
    "TABLE_NAME": "[cbc]",
    "COLUMN_NAME": {
        "PATIENT_ID": "[patientid]",
        "REQ_DATE": "[requestdate]",
        "HGB": "[hgb]",
        "HCT": "[hct]",
        "MCHC": "[mchc]",
    },
    "CONDITION": {"PATIENT_ID": "[patientid]"},
}

# Define tables and columns for retrieving patient information
PATIENT_INFO_SQL = {
    "DB_NAME": "[patients]",
    "TABLE_NAME": "[patientinfo]",
    "COLUMN_NAME": {
        "NAME": "[patientnamear]",
        "SEX": "[patientsex]",
        "AGE": "[patientage]",
        "AGE_UNIT": "[patientageunit]",
        "REQ_DATE": "[requestdate]",
    },
    "CONDITION": {"PATIENT_ID": "[patientid]"},
}

# Define tables and columns for retrieving the patient's waiting list for tests based on test code
PATIENT_TEST_SQL = {
    "DB_NAME": "[patients]",
    "TABLE_NAME": "[patienttest]",
    "COLUMN_NAME": {"TEST_CODE": "[testcode]", "RESULT_STATE": "[resultfinsh]"},
    "CONDITION": {"PATIENT_ID": "[patientid]"},
    "RETURN_ALL": True,
}






# This dictionary maps a key to a stored procedure definition.
# The definition includes the procedure name and the expected parameters.


# Used in: gui/views/patient.py
PATIENT_SEARCH_SQL = {
    "PROCEDURE_NAME": "dbo.GetPatientInfo",
    "PARAMETERS": [
        "PATIENT_ID",
        "PATIENT_NAME",
        "START_DATE",
        "END_DATE",
        "RESULT_FINISHED",
    ],
}

# Used in: gui/views/cbc_report.py
PATIENT_CBC_RESULT_SQL = {
    "PROCEDURE_NAME": "dbo.GetPatientCBCResult",
    "PARAMETERS": ["PATIENT_ID"],
}

# Used in: gui/views/send_out.py
SEND_OUT_SEARCH_SQL = {
    "PROCEDURE_NAME": "dbo.GetSendOutSamples",
    "PARAMETERS": ["PatientID", "PatientName", "StartDate", "EndDate", "DestinationLab", "Status"],
}

# Used in: gui/views/send_out.py for the "Mark as Sent" button
INSERT_SEND_OUT_LOG_SQL = {
    "PROCEDURE_NAME": "dbo.InsertSendOutLog",
    "PARAMETERS": ["PatientID", "TestName", "SentDate"],
}

# Used in: gui/views/send_out.py
GET_DESTINATION_LABS_SQL = {
    "PROCEDURE_NAME": "dbo.GetDestinationLabs",
    "PARAMETERS": [],
}

# Used in: gui/views/send_out.py for editing Price and Amount Paid
UPDATE_SEND_OUT_FINANCIALS_SQL = {
    "PROCEDURE_NAME": "dbo.UpdateSendOutFinancials",
    "PARAMETERS": ["PatientID", "TestName", "Price", "AmountPaid", "DestinationLab", "EditDate", "Status"],
}
