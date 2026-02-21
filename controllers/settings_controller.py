"""
Controller for the settings tab functionality.
"""

from tkinter import messagebox

from views.dialogs.credential_dialog import CredentialListManager
from utils.config_manager import get_api_key, save_api_key

class SettingsController:
    """
    Controller for the Settings tab functionality.
    """

    def __init__(self, view, credentials_model):
        """
        Initialize the settings controller.

        Args:
            view: The settings view
            credentials_model: The credentials model
        """
        self.view = view
        self.credentials_model = credentials_model

        self._setup_callbacks()
        self._setup_observers()
        self._init_view()

    def _setup_callbacks(self):
        """Set up UI callbacks."""
        self.view.set_callback("save_api_key", self.save_api_key)
        self.view.set_callback("manage_credentials", self.manage_credentials)

    def _setup_observers(self):
        """Set up model change observers."""
        self.credentials_model.add_observer(self._update_credentials_count)

    def _init_view(self):
        """Initialize the view with current settings."""
        self.view.set_api_key(get_api_key())
        self._update_credentials_count()

    def _update_credentials_count(self):
        """Update the credentials count in the view."""
        count = self.credentials_model.get_credentials_count()
        self.view.set_credentials_count(count)

    def save_api_key(self):
        """Save the API key from the view."""
        api_key = self.view.get_api_key()

        if not api_key:
            messagebox.showerror("Error", "API Key cannot be empty")
            return

        save_api_key(api_key)

        messagebox.showinfo("Success", "API Key saved successfully")

    def manage_credentials(self):
        """Open dialog to manage switch credentials."""
        dialog = CredentialListManager(self.view.parent, self.credentials_model.get_credentials())
        self.view.parent.wait_window(dialog)

        if dialog.result is not None:
            self.credentials_model.clear_credentials()

            for cred in dialog.result:
                self.credentials_model.add_credential(cred)

            count = len(dialog.result)
            if count == 0:
                messagebox.showinfo("Success", "All credentials removed")
            elif count == 1:
                messagebox.showinfo("Success", "1 credential saved")
            else:
                messagebox.showinfo("Success", f"{count} credentials saved")
