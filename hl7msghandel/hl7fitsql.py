from log.logger import log_info, log_error
from copy import deepcopy

# Define the source for logging purposes
SOURCE = "HL7Message"


def update_hl7_dictionary(hl7_message, hl7_dictionary, sql_data=None, manual_data=None):
    """
    Updates the HL7 dictionary with the provided message and dictionary.

    Args:
        hl7_message: The HL7 message object from which the values are extracted.
        hl7_dictionary: The HL7 dictionary that needs to be updated.
        sql_data: Optional dictionary containing SQL data to update the dictionary (default is None).
        manual_data: Optional dictionary containing manual data to update the dictionary (default is None).

    Returns:
        The updated HL7 dictionary.
    """
    # Create a deep copy of the HL7 dictionary to avoid modifying the original
    hl7_dictionary_copy = deepcopy(hl7_dictionary)

    result_dictionary = hl7_dictionary_copy["COLUMN_NAME"]
    condition_dictionary = hl7_dictionary_copy["CONDITION"]

    result_dictionary_deleted_list = []

    # Iterate through the result dictionary to update values
    for key, value in result_dictionary.items():
        if value == "SQL":
            try:
                # Update the result dictionary with SQL data if provided
                if sql_data is not None:
                    result_dictionary[key] = sql_data[key]
            except Exception as e:
                log_error(f"Error updating sql dictionary: {e}", source=SOURCE)

        elif value == "MANUAL":
            try:
                # Update the result dictionary with manual data if provided
                if manual_data is not None:
                    result_dictionary[key] = manual_data[key]
                result_dictionary_deleted_list.append(key)
            except Exception as e:
                log_error(f"Error updating manual dictionary: {e}", source=SOURCE)

        else:
            try:
                # Extract values from the HL7 message for other keys
                segment = result_dictionary[key]["S"]
                s_number = int(result_dictionary[key]["N"])
                field = int(result_dictionary[key]["F"])
                result_value = hl7_message.segments(segment)[s_number][field]
                result_dictionary[key] = result_value
            except Exception as e:
                log_error(f"Error updating condition dictionary: {e}", source=SOURCE)

    # Remove keys from the result dictionary that were marked for deletion
    for result in result_dictionary_deleted_list:
        try:
            del result_dictionary[result]
        except Exception as e:
            log_error(f"Error deleting empty result dictionary: {e}", source=SOURCE)

    # Update the condition dictionary with values from the HL7 message
    for key in condition_dictionary.keys():
        try:
            segment = condition_dictionary[key]["S"]
            s_number = int(condition_dictionary[key]["N"])
            field = int(condition_dictionary[key]["F"])
            condition_value = hl7_message.segments(segment)[s_number][field]
            condition_dictionary[key] = condition_value
        except Exception as e:
            log_error(f"Error updating condition dictionary: {e}", source=SOURCE)

    return hl7_dictionary_copy
