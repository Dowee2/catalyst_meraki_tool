"""
Model for managing Meraki serial numbers.
"""

class SerialsModel:
    """
    Handles storage and retrieval of Meraki switch serial numbers.

    Serial numbers can be managed separately for different operations.
    """

    def __init__(self):
        """Initialize the serials model."""
        self._serials = {
            "convert": [],
            "interface": [],
            "mac": []
        }
        self._observers = {}

        for context in self._serials.keys():
            self._observers[context] = []

    def add_serial(self, context, serial):
        """
        Add a new serial number to the list for a specific context.

        Args:
            context (str): The context for the serial (convert, interface, mac)
            serial (str): The serial number to add

        Returns:
            bool: True if the serial was added, False otherwise
        """
        if context not in self._serials:
            return False

        if not serial or not isinstance(serial, str):
            return False

        serial = serial.strip()
        if serial and serial not in self._serials[context]:
            self._serials[context].append(serial)
            self._notify_observers(context)
            return True

        return False

    def update_serial(self, context, index, serial):
        """
        Update an existing serial number.

        Args:
            context (str): The context for the serial
            index (int): The index of the serial to update
            serial (str): The new serial number

        Returns:
            bool: True if the serial was updated, False otherwise
        """
        if context not in self._serials:
            return False

        if not 0 <= index < len(self._serials[context]):
            return False

        if not serial or not isinstance(serial, str):
            return False

        serial = serial.strip()
        if serial:
            self._serials[context][index] = serial
            self._notify_observers(context)
            return True

        return False

    def remove_serial(self, context, index):
        """
        Remove a serial number.

        Args:
            context (str): The context for the serial
            index (int): The index of the serial to remove

        Returns:
            bool: True if the serial was removed, False otherwise
        """
        if context not in self._serials:
            return False

        if not 0 <= index < len(self._serials[context]):
            return False

        del self._serials[context][index]
        self._notify_observers(context)
        return True

    def get_serials(self, context):
        """
        Get all serial numbers for a specific context.

        Args:
            context (str): The context to get serials for

        Returns:
            list: List of serial numbers
        """
        if context not in self._serials:
            return []

        return self._serials[context].copy()

    def move_serial(self, context, from_index, to_index):
        """
        Move a serial number from one position to another.

        Args:
            context (str): The context for the serial
            from_index (int): The current index of the serial
            to_index (int): The new index for the serial

        Returns:
            bool: True if the serial was moved, False otherwise
        """
        if context not in self._serials:
            return False

        serials = self._serials[context]
        if not 0 <= from_index < len(serials) or not 0 <= to_index < len(serials):
            return False

        serial = serials.pop(from_index)
        serials.insert(to_index, serial)
        self._notify_observers(context)
        return True

    def set_serials(self, context, serials):
        """
        Set the entire list of serial numbers for a context.

        Args:
            context (str): The context to set serials for
            serials (list): List of serial numbers

        Returns:
            bool: True if the serials were set, False otherwise
        """
        if context not in self._serials:
            return False

        if not isinstance(serials, list):
            return False

        clean_serials = []
        for serial in serials:
            if isinstance(serial, str) and serial.strip():
                clean_serials.append(serial.strip())

        self._serials[context] = clean_serials
        self._notify_observers(context)
        return True

    def get_contexts(self):
        """
        Get all available contexts.

        Returns:
            list: List of context names
        """
        return list(self._serials.keys())

    def add_observer(self, context, observer):
        """
        Add an observer for serial changes in a specific context.

        Args:
            context (str): The context to observe
            observer: A function to call when serials change
        """
        if context not in self._observers:
            self._observers[context] = []

        if observer not in self._observers[context]:
            self._observers[context].append(observer)

    def remove_observer(self, context, observer):
        """
        Remove an observer.

        Args:
            context (str): The context the observer is for
            observer: The observer to remove
        """
        if context in self._observers and observer in self._observers[context]:
            self._observers[context].remove(observer)

    def _notify_observers(self, context):
        """
        Notify all observers of a change in a specific context.

        Args:
            context (str): The context that changed
        """
        if context in self._observers:
            for observer in self._observers[context]:
                observer()