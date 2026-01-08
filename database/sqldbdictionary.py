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
