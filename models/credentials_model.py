"""
Model for managing switch credentials.
"""

class CredentialsModel:
    """
    Handles storage and retrieval of switch credentials.
    
    Credentials are stored in memory only for security reasons.
    """
    
    def __init__(self):
        """Initialize the credentials model."""
        self._credentials = []
        self._observers = []

    def _is_valid_credential(self, credential):
        """
        Check if a credential is valid.

        Args:
            credential: The credential to validate

        Returns:
            bool: True if valid (non-null dict with required keys), False otherwise
        """
        if not credential or not isinstance(credential, dict):
            return False
        if 'username' not in credential or 'password' not in credential:
            return False
        return True

    def _ensure_description(self, credential):
        """
        Ensure the credential has a description, adding a default if needed.

        Args:
            credential (dict): The credential to check
        """
        if 'description' not in credential or not credential['description']:
            credential['description'] = f"{credential['username']} credential"

    def add_credential(self, credential):
        """
        Add a new credential to the list.
        
        Args:
            credential (dict): Dictionary containing username, password, and description
            
        Returns:
            bool: True if the credential was added, False otherwise
        """
        if not self._is_valid_credential(credential):
            return False

        self._ensure_description(credential)
        self._credentials.append(credential)
        self._notify_observers()
        return True
    
    def update_credential(self, index, credential):
        """
        Update an existing credential.
        
        Args:
            index (int): The index of the credential to update
            credential (dict): The new credential data
            
        Returns:
            bool: True if the credential was updated, False otherwise
        """
        if not 0 <= index < len(self._credentials):
            return False

        if not self._is_valid_credential(credential):
            return False

        self._ensure_description(credential)
        self._credentials[index] = credential
        self._notify_observers()
        return True
    
    def remove_credential(self, index):
        """
        Remove a credential.
        
        Args:
            index (int): The index of the credential to remove
            
        Returns:
            bool: True if the credential was removed, False otherwise
        """
        if not 0 <= index < len(self._credentials):
            return False
            
        del self._credentials[index]
        self._notify_observers()
        return True
    
    def get_credentials(self):
        """
        Get all credentials.
        
        Returns:
            list: List of credential dictionaries
        """
        return self._credentials.copy()
    
    def get_credential(self, index):
        """
        Get a specific credential.
        
        Args:
            index (int): The index of the credential to get
            
        Returns:
            dict or None: The credential dictionary or None if not found
        """
        if not 0 <= index < len(self._credentials):
            return None
            
        return self._credentials[index].copy()
    
    def get_credentials_count(self):
        """
        Get the number of stored credentials.
        
        Returns:
            int: The number of credentials
        """
        return len(self._credentials)
    
    def clear_credentials(self):
        """
        Clear all credentials.
        
        Returns:
            bool: True if credentials were cleared
        """
        self._credentials = []
        self._notify_observers()
        return True
    
    def add_observer(self, observer):
        """
        Add an observer for credential changes.
        
        Args:
            observer: A function to call when credentials change
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer):
        """
        Remove an observer.
        
        Args:
            observer: The observer to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self):
        """Notify all observers of a change."""
        for observer in self._observers:
            observer()