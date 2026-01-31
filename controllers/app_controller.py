"""
Main application controller for the Catalyst to Meraki Migration Tool.
"""

import os
import tkinter as tk
from tkinter import messagebox

from views.main_window import MainWindow
from views.conversion_view import ConversionView
from views.interface_compare_view import InterfaceCompareView
from views.mac_compare_view import MacCompareView
from views.settings_view import SettingsView

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
        
        # Create main window and view controllers
        self.main_window = MainWindow(root)
        
        # Create views
        self._init_views()
        
        # Create child controllers
        self._init_controllers()
        
        # Check if API key is set
        self._check_api_key()
    
    def _init_views(self):
        """Initialize all the view components."""
        # Create tab views
        self.conversion_view = ConversionView(self.main_window.get_tab_frame("convert"))
        self.interface_view = InterfaceCompareView(self.main_window.get_tab_frame("interface"))
        self.mac_view = MacCompareView(self.main_window.get_tab_frame("mac"))
        self.settings_view = SettingsView(self.main_window.get_tab_frame("settings"))
        
        # Register views with main window
        self.main_window.register_view("convert", self.conversion_view)
        self.main_window.register_view("interface", self.interface_view)
        self.main_window.register_view("mac", self.mac_view)
        self.main_window.register_view("settings", self.settings_view)
    
    def _init_controllers(self):
        """Initialize child controllers."""
        # Create controllers
        self.conversion_controller = ConversionController(
            self.conversion_view,
            self.credentials_model,
            self.serials_model,
            self.modules
        )
        
        self.comparison_controller = ComparisonController(
            self.interface_view,
            self.mac_view,
            self.credentials_model,
            self.serials_model,
            self.switch_data_model,
            self.modules
        )
        
        self.settings_controller = SettingsController(
            self.settings_view,
            self.credentials_model
        )
        
        # Set initial status
        self.main_window.set_status("Ready")
    
    def _check_api_key(self):
        """Check if API key is set and prompt if needed."""
        api_key = os.getenv("MERAKI_DASHBOARD_API_KEY", "")
        
        # Update settings view with API key
        self.settings_view.set_api_key(api_key)
        
        if not api_key:
            # Show API key dialog after a short delay
            self.root.after(500, self._show_api_key_dialog)
    
    def _show_api_key_dialog(self):
        """Show a dialog for entering the API key."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Meraki API Key Required")
        dialog.geometry("500x250")
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
        
        # Save API key to environment variable
        os.environ["MERAKI_DASHBOARD_API_KEY"] = api_key.strip()
        
        # Update settings view
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
        api_key = os.getenv("MERAKI_DASHBOARD_API_KEY", "")
        if not api_key:
            # Show warning
            if messagebox.askokcancel("Warning", 
                                     "No API key provided. Some functions may not work correctly.\n\n"
                                     "Do you want to continue without an API key?", 
                                     parent=dialog):
                dialog.destroy()
        else:
            dialog.destroy()