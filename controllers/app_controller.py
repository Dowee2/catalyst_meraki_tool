"""
Main application controller for the Catalyst to Meraki Migration Tool.
"""

import os
import tkinter as tk
from tkinter import messagebox

from views.main_window import MainWindow
from views.dashboard_view import DashboardView
from views.settings_view import SettingsView
from views.wizards.conversion_wizard import ConversionWizard
from views.wizards.comparison_wizard import ComparisonWizard

from controllers.conversion_controller import ConversionController
from controllers.comparison_controller import ComparisonController
from controllers.settings_controller import SettingsController

from models.credentials_model import CredentialsModel
from models.serials_model import SerialsModel
from models.switch_data_model import SwitchDataModel

from utils.script_loader import ScriptLoader


class AppController:
    """
    Main application controller that coordinates all the other controllers and models.
    """

    def __init__(self, root):
        """
        Initialize the application controller.

        Args:
            root: The tkinter root window
        """
        self.root = root

        # Initialize models
        self.credentials_model = CredentialsModel()
        self.serials_model = SerialsModel()
        self.switch_data_model = SwitchDataModel()

        # Load script modules
        self.script_loader = ScriptLoader()
        self.modules = self.script_loader.load_scripts()

        if not self.modules:
            messagebox.showerror("Error", "Failed to load required script modules.\n"
                                "Please make sure all script files are in the correct location.")
            root.destroy()
            return

        # Create main window
        self.main_window = MainWindow(root)
        self.main_window.set_back_to_dashboard_callback(self._show_dashboard)

        # Create controllers for wizard-based operations
        self.conversion_controller = ConversionController(
            credentials_model=self.credentials_model,
            serials_model=self.serials_model,
            modules=self.modules
        )

        self.comparison_controller = ComparisonController(
            credentials_model=self.credentials_model,
            serials_model=self.serials_model,
            switch_data_model=self.switch_data_model,
            modules=self.modules
        )

        # Settings view will be created on-demand
        self.settings_view = None
        self.settings_controller = None

        # Create and show dashboard
        self._create_dashboard()
        self._show_dashboard()

        # Check if API key is set
        self._check_api_key()

    def _create_dashboard(self):
        """Create the dashboard view."""
        self.dashboard = DashboardView(
            self.main_window.get_content_frame(),
            on_migrate=self._on_migrate_clicked,
            on_compare=self._on_compare_clicked,
            on_settings=self._on_settings_clicked
        )

    def _show_dashboard(self):
        """Show the dashboard."""
        # Destroy any existing wizard views to free memory
        if hasattr(self, '_current_wizard') and self._current_wizard:
            self._current_wizard.destroy()
            self._current_wizard = None

        self.main_window.show_dashboard(self.dashboard)

    def _on_migrate_clicked(self):
        """Handle Migrate card click on dashboard."""
        # Create a new conversion wizard
        wizard = ConversionWizard(
            self.main_window.get_content_frame(),
            credentials_model=self.credentials_model,
            serials_model=self.serials_model,
            on_complete=self._on_conversion_complete,
            on_cancel=self._on_wizard_cancel
        )
        self._current_wizard = wizard
        self.main_window.show_conversion_wizard(wizard)

    def _on_compare_clicked(self):
        """Handle Compare card click on dashboard."""
        # Create a new comparison wizard
        wizard = ComparisonWizard(
            self.main_window.get_content_frame(),
            credentials_model=self.credentials_model,
            serials_model=self.serials_model,
            switch_data_model=self.switch_data_model,
            on_complete=self._on_comparison_complete,
            on_cancel=self._on_wizard_cancel
        )
        self._current_wizard = wizard
        self.main_window.show_comparison_wizard(wizard)

    def _on_settings_clicked(self):
        """Handle Settings card click on dashboard."""
        self.main_window.show_settings(self._create_settings_view)

    def _create_settings_view(self, parent):
        """
        Factory function to create the settings view.

        Args:
            parent: Parent frame for the settings view

        Returns:
            SettingsView: The created settings view
        """
        self.settings_view = SettingsView(parent)
        self.settings_controller = SettingsController(
            self.settings_view,
            self.credentials_model
        )

        # Set API key if available
        api_key = os.getenv("MERAKI_DASHBOARD_API_KEY", "") or os.getenv("MERAKI_API_KEY", "")
        if api_key:
            self.settings_view.set_api_key(api_key)

        return self.settings_view

    def _on_wizard_cancel(self):
        """Handle wizard cancellation."""
        self._show_dashboard()

    def _on_conversion_complete(self, wizard_data):
        """
        Handle conversion wizard completion.

        Args:
            wizard_data (dict): Data collected from the wizard
        """
        # Run the conversion using the controller
        self.conversion_controller.run_conversion(
            wizard_data,
            console_widget=self._current_wizard.get_console()
        )

    def _on_comparison_complete(self, wizard_data):
        """
        Handle comparison wizard completion.

        Args:
            wizard_data (dict): Data collected from the wizard
        """
        # The comparison wizard handles its own comparison in Step 3
        # This callback is for when the wizard is fully finished
        pass

    def _check_api_key(self):
        """Check if API key is set and prompt if needed."""
        api_key = os.getenv("MERAKI_DASHBOARD_API_KEY", "")

        # Also check MERAKI_API_KEY
        if not api_key:
            api_key = os.getenv("MERAKI_API_KEY", "")

        # Update settings view with API key (if it exists)
        if self.settings_view:
            self.settings_view.set_api_key(api_key)

        if not api_key:
            # Show API key dialog after a short delay
            self.root.after(500, self._show_api_key_dialog)

    def _show_api_key_dialog(self):
        """Show a dialog for entering the API key."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Meraki API Key Required")
        dialog.geometry("500x350")
        dialog.transient(self.root)
        dialog.grab_set()

        # Make the dialog modal
        dialog.focus_set()
        dialog.protocol("WM_DELETE_WINDOW", lambda: self._on_api_dialog_close(dialog))

        # Create dialog content
        frame = tk.Frame(dialog, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Add explanation
        explanation = """
        A Meraki API key is required to use this application.

        You can generate an API key in the Meraki Dashboard
        under your profile (Organization > My Profile).
        """
        tk.Label(frame, text=explanation, justify=tk.LEFT, wraplength=450).pack(anchor=tk.W, pady=10)

        # API Key entry
        key_frame = tk.Frame(frame)
        key_frame.pack(fill=tk.X, pady=10)

        tk.Label(key_frame, text="API Key:").pack(side=tk.LEFT)
        api_key_var = tk.StringVar()
        api_key_entry = tk.Entry(key_frame, textvariable=api_key_var, width=50)
        api_key_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # Buttons
        button_frame = tk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)

        tk.Button(button_frame, text="Save",
                 command=lambda: self._save_api_key(dialog, api_key_var.get())
                 ).pack(side=tk.RIGHT, padx=5)

        # Focus on entry field
        api_key_entry.focus_set()

    def _save_api_key(self, dialog, api_key):
        """
        Save the API key and close the dialog.

        Args:
            dialog: The dialog window
            api_key (str): The API key to save
        """
        if not api_key.strip():
            messagebox.showwarning("Warning", "API Key cannot be empty.", parent=dialog)
            return

        # Save API key to environment variables (both names for compatibility)
        os.environ["MERAKI_DASHBOARD_API_KEY"] = api_key.strip()
        os.environ["MERAKI_API_KEY"] = api_key.strip()

        # Update settings view (if it exists)
        if self.settings_view:
            self.settings_view.set_api_key(api_key.strip())

        # Close dialog
        dialog.destroy()

        # Update status
        self.main_window.set_status("API Key saved")

    def _on_api_dialog_close(self, dialog):
        """
        Handle dialog close event.

        Args:
            dialog: The dialog window
        """
        # Check if API key is set
        api_key = os.getenv("MERAKI_DASHBOARD_API_KEY", "") or os.getenv("MERAKI_API_KEY", "")
        if not api_key:
            # Show warning
            if messagebox.askokcancel("Warning",
                                     "No API key provided. Some functions may not work correctly.\n\n"
                                     "Do you want to continue without an API key?",
                                     parent=dialog):
                dialog.destroy()
        else:
            dialog.destroy()
