"""
Model for tracking migration progress.
"""
import json
import os

class ProgressModel:
    """
    Tracks the progress of switch migrations.
    """

    def __init__(self, file_path="migration_progress.json"):
        """
        Initialize the progress model.

        Args:
            file_path (str): Path to the progress file
        """
        self._file_path = file_path
        self._switches = {}
        self._observers = []

        self._load_progress()

    def _load_progress(self):
        """Load progress from file if it exists."""
        if os.path.exists(self._file_path):
            try:
                with open(self._file_path, 'r') as f:
                    self._switches = json.load(f)
            except Exception:
                self._switches = {}

    def _save_progress(self):
        """Save progress to file."""
        try:
            with open(self._file_path, 'w') as f:
                json.dump(self._switches, f, indent=2)
        except Exception:
            pass

        self._notify_observers()

    def update_switch_progress(self, switch_ip, hostname, status):
        """
        Update the progress for a switch.

        Args:
            switch_ip (str): The switch IP address
            hostname (str): The switch hostname
            status (dict): Dictionary with status information
        """
        self._switches[switch_ip] = {
            'hostname': hostname,
            'status': status
        }
        self._save_progress()

    def get_switch_progress(self, switch_ip):
        """
        Get the progress for a switch.

        Args:
            switch_ip (str): The switch IP address

        Returns:
            dict or None: The switch progress or None if not found
        """
        return self._switches.get(switch_ip)

    def get_all_switches(self):
        """
        Get all tracked switches.

        Returns:
            dict: Dictionary of all switches and their progress
        """
        return self._switches.copy()

    def add_observer(self, observer):
        """
        Add an observer for progress changes.

        Args:
            observer: A function to call when progress changes
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