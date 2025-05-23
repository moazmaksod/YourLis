import abc
from typing import Dict, List, Any, Union

class DatabaseAdapter(abc.ABC):
    """
    Abstract base class for database adapters.
    Defines a common interface for database operations.
    """

    @abc.abstractmethod
    def connect(self, connection_params: Dict[str, Any]) -> None:
        """
        Establishes a connection to the database.

        Args:
            connection_params: A dictionary of parameters needed to connect
                               to the database (e.g., host, port, user, password,
                               database name).
        """
        pass

    @abc.abstractmethod
    def disconnect(self) -> None:
        """
        Closes the connection to the database.
        """
        pass

    @abc.abstractmethod
    def is_connected(self) -> bool:
        """
        Checks if a connection to the database is currently active.

        Returns:
            True if connected, False otherwise.
        """
        pass

    @abc.abstractmethod
    def check_result_exists(self, patient_id: str) -> bool:
        """
        Checks if a test result exists for a given patient.

        Args:
            patient_id: The unique identifier of the patient.

        Returns:
            True if a result exists, False otherwise.
        """
        pass

    @abc.abstractmethod
    def save_cbc_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None:
        """
        Saves a Complete Blood Count (CBC) test result for a patient.

        Args:
            patient_id: The unique identifier of the patient.
            result_data: A dictionary containing the CBC results (e.g., {'HGB': 12.5, 'RBC': 4.5}).
            request_date: The date of the test request in 'YYYY-MM-DD HH:MM:SS' format.
        """
        pass

    @abc.abstractmethod
    def update_cbc_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None:
        """
        Updates an existing Complete Blood Count (CBC) test result for a patient.

        Args:
            patient_id: The unique identifier of the patient.
            result_data: A dictionary containing the updated CBC results.
            request_date: The date of the test request in 'YYYY-MM-DD HH:MM:SS' format.
        """
        pass

    @abc.abstractmethod
    def save_hgb_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None:
        """
        Saves a Hemoglobin (HGB) test result for a patient.

        Args:
            patient_id: The unique identifier of the patient.
            result_data: A dictionary containing the HGB result (e.g., {'HGB': 12.5}).
            request_date: The date of the test request in 'YYYY-MM-DD HH:MM:SS' format.
        """
        pass

    @abc.abstractmethod
    def update_hgb_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None:
        """
        Updates an existing Hemoglobin (HGB) test result for a patient.

        Args:
            patient_id: The unique identifier of the patient.
            result_data: A dictionary containing the updated HGB result.
            request_date: The date of the test request in 'YYYY-MM-DD HH:MM:SS' format.
        """
        pass

    @abc.abstractmethod
    def get_patient_info(self, patient_id: str) -> Union[Dict[str, Any], None]:
        """
        Retrieves patient information.

        Args:
            patient_id: The unique identifier of the patient.

        Returns:
            A dictionary containing patient information if found, None otherwise.
        """
        pass

    @abc.abstractmethod
    def get_patient_test_request(self, patient_id: str) -> Union[Dict[str, Any], None]:
        """
        Retrieves test request information for a patient.

        Args:
            patient_id: The unique identifier of the patient.

        Returns:
            A dictionary containing test request information if found, None otherwise.
        """
        pass

    @abc.abstractmethod
    def execute_procedure(self, procedure_name: str, params: Dict[str, Any]) -> Union[List[Dict[str, Any]], None]:
        """
        Executes a stored procedure in the database.

        Args:
            procedure_name: The name of the stored procedure to execute.
            params: A dictionary of parameters to pass to the stored procedure.

        Returns:
            A list of dictionaries representing the rows returned by the procedure,
            or None if the procedure does not return results or an error occurs.
        """
        pass
