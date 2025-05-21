# Configure HL7 message data address to DB schema
# Item format:
# {
#     "DB_NAME" : '[DB_NAME]',
#     "TABLE_NAME" : '[TABLE_NAME]',
#     "COLUMN_NAME" : {
#         "ITEM_NAME" :'[COLUMN_NAME]',
#         "ANOTHER_ITEM_NAME" :'[COLUMN_NAME]'
#     },
#     "CONDITION" : {
#         "CONDITION_NAME" : '[COLUMN_NAME]',
#         "ANOTHER_CONDITION_NAME" : '[COLUMN_NAME]'
#     }
# }

from log.logger import log_info
# Define SOURCE for logging purposes
SOURCE = "HL7Message"
log_info("Loading HL7 schema definitions...", source=SOURCE)



# Define tables and columns for select exist test for patient to update or insert
RESULT_EXIST_HL7 = {
    "COLUMN_NAME" : {
        "PATIENT_ID" : "SQL"
    },
    "CONDITION" : {
        "PATIENT_ID" : {
            'S' : 'PID',
            'N' : '0',
            'F' : '3'
        }
    }
}
log_info("Loaded HL7 message schema for check if there is a record for the patient id before.", source=SOURCE)

# Define tables and columns for CBC results to insert or update
CBC_RESULT_HL7 = {
    "COLUMN_NAME" : {
        "PATIENT_ID" : {
            'S' : 'PID',
            'N' : '0',
            'F' : '3'
        },
        "REQ_DATE" :"SQL",
        "HGB" : {
            "S" : 'OBX',
            "N" : '8',
            "F" : '5',
        },
        "RBC" : {
            "S" : 'OBX',
            "N" : '7',
            "F" : '5',
        },
        "HCT" : {
            "S" : 'OBX',
            "N" : '9',
            "F" : '5',
        },
        "PLT" : {
            "S" : 'OBX',
            "N" : '15',
            "F" : '5',
        },
        "HGB%" : 'MANUAL',
        "MCV" : {
            "S" : 'OBX',
            "N" : '10',
            "F" : '5',
        },
        "MCH" : {
            "S" : 'OBX',
            "N" : '11',
            "F" : '5',
        },
        "MCHC" : {
            "S" : 'OBX',
            "N" : '12',
            "F" : '5',
        },
        "PCT" : {
            "S" : 'OBX',
            "N" : '18',
            "F" : '5',
        },
        "MPV" : {
            "S" : 'OBX',
            "N" : '16',
            "F" : '5',
        },
        "WBC" : {
            "S" : 'OBX',
            "N" : '0',
            "F" : '5',
        },
        "NEUTROPHIL" : {
            "S" : 'OBX',
            "N" : '6',
            "F" : '5',
        },
        "LYMPHOCYTE" : {
            "S" : 'OBX',
            "N" : '4',
            "F" : '5',
        },
        "MONOCYTE" : {
            "S" : 'OBX',
            "N" : '5',
            "F" : '5',
        },
        "EOSINOPHIL" : 'MANUAL',
        "BASOPHIL" : 'MANUAL',
        "OTHERCELL" : 'MANUAL',
        "RDW" : {
            "S" : 'OBX',
            "N" : '13',
            "F" : '5',
        },
        "PDW" : {
            "S" : 'OBX',
            "N" : '17',
            "F" : '5',
        },
        "SEGMENT" : 'MANUAL',
        "BAND" : 'MANUAL',
        "COMMENT" : 'MANUAL',
        "JUVENILE" : 'MANUAL',
        "MYELOCYTES" : 'MANUAL',
        "PROMYELOCYTE" : 'MANUAL',
        "BLAST" : 'MANUAL',
        "NRBCWBC" : 'MANUAL'
    },
    "CONDITION" : {
        "PATIENT_ID" : {
            'S' : 'PID',
            'N' : '0',
            'F' : '3'
        }
    }
}
log_info("Loaded HL7 message schema for CBC results.", source=SOURCE)

# Define tables and columns for Hgb results to insert or update
HGB_RESULT_HL7 = {
    "COLUMN_NAME" : {
        "PATIENT_ID" : {
            'S' : 'PID',
            'N' : '0',
            'F' : '3'
        },
        "REQ_DATE" :"SQL",
        "HGB" : {
            "S" : 'OBX',
            "N" : '8',
            "F" : '5',
        },
        "HCT" : {
            "S" : 'OBX',
            "N" : '9',
            "F" : '5',
        },
        "MCHC" : {
            "S" : 'OBX',
            "N" : '12',
            "F" : '5',
        }
    },
    "CONDITION" : {
        "PATIENT_ID" : {
            'S' : 'PID',
            'N' : '0',
            'F' : '3'
        }
    }
}
log_info("Loaded HL7 message schema for HGB results.", source=SOURCE)

# Define tables and columns for getting the patient info (ORU HL7)
PATIENT_INFO_ORU_HL7 = {
    "COLUMN_NAME" : {
        "NAME" :'SQL',
        "SEX" :'SQL',
        "AGE" :'SQL',
        "AGE_UNIT" :'SQL',
        "REQ_DATE" :'SQL'
    },
    "CONDITION" : {
        "PATIENT_ID" : {
            "S" : 'PID',
            "N" : '0',
            "F" : '3',
        }
    }
}
log_info("Loaded HL7 message schema for patient info from result message.", source=SOURCE)

# Define tables and columns for getting the patient info (ORM HL7)
PATIENT_INFO_ORM_HL7 = {
    "COLUMN_NAME" : {
        "NAME" :'SQL',
        "SEX" :'SQL',
        "AGE" :'SQL',
        "AGE_UNIT" :'SQL',
        "REQ_DATE" :'SQL'
    },
    "CONDITION" : {
        "PATIENT_ID" : {
            "S" : 'ORC',
            "N" : '0',
            "F" : '3',
        }
    }
}
log_info("Loaded HL7 message schema for patient info from request message.", source=SOURCE)

# Dictionary for converting SQL to HL7 values
PATIENT_INFO_SQL_TO_HL7_DICT = {
    'Male' : 'M',
    'Female' : 'F',
    'Years' : '1',
    'Mons.' : '2',
    'Days' : '3',
    'Hours' : '4'
}
log_info("Loaded HL7 schema for convert info symbol from sql .", source=SOURCE)

# Default values for patient info if not found
DEFULT_PATIENT_INFO_HL7 = {
    "NAME" :'Patient Not in DB',
    "SEX" :'M',
    "AGE" :'30',
    "AGE_UNIT" :'1'
}
log_info("Loaded HL7 default patient info.", source=SOURCE)

# Define tables and columns for patient test waiting list based on test code
PATIENT_TEST_HL7 = {
    "COLUMN_NAME" : {
        "TEST_CODE" : 'SQL',
        "RESULT_STATE" : 'SQL'
    },
    "CONDITION" : {
        "PATIENT_ID" : {
            'S' : 'PID',
            'N' : '0',
            'F' : '3'
        }
    }
}
log_info("Loaded HL7 message schema for patient requested test waiting list.", source=SOURCE)