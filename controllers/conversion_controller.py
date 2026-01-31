"""
Controller for the conversion tab functionality.
"""

import os
import traceback
from tkinter import messagebox

from views.dialogs.credential_dialog import CredentialSelector
from views.dialogs.serial_dialog import SerialListManager
from utils.workers import BackgroundTask
from config.script_types import ScriptType

class ConversionController:
    """
    Controller for the Convert Config tab functionality.
    """
    
    def __init__(self, view, credentials_model, serials_model, modules):
        """
        Initialize the conversion controller.
        
        Args:
            view: The conversion view
            credentials_model: The credentials model
            serials_model: The serials model
            modules: Dictionary of loaded script modules
        """
        self.view = view
        self.credentials_model = credentials_model
        self.serials_model = serials_model
        self.modules = modules
        
        # Set up callbacks
        self._setup_callbacks()
        
        # Set up model observers
        self._setup_observers()
        
        # Update UI with initial data
        self._update_serials_display()
    
    def _setup_callbacks(self):
        """Set up UI callbacks."""
        self.view.set_callback("start_conversion", self.start_conversion)
        self.view.set_callback("manage_credentials", self.manage_credentials)
        self.view.set_callback("manage_serials", self.manage_serials)
        self.view.set_callback("browse_config", self.browse_config_file)
    
    def _setup_observers(self):
        """Set up model change observers."""
        # Observe serials model for the conversion context
        self.serials_model.add_observer("convert", self._update_serials_display)
    
    def _update_serials_display(self):
        """Update the serials display from the model."""
        serials = self.serials_model.get_serials("convert")
        self.view.set_serials_display(serials)
    
    def start_conversion(self):
        """Start the conversion process."""
        # Check if API key is set
        api_key = os.getenv("MERAKI_API_KEY")
        if not api_key:
            messagebox.showerror("Error", "Meraki API Key is not set. Please set it in the Settings tab.")
            return
        
        # Get Meraki serials
        meraki_serials = self.serials_model.get_serials("convert")
        if not meraki_serials:
            messagebox.showerror("Error", "Meraki serial numbers are required.")
            return
        
        # Get source type
        source_type = self.view.get_source_type()
        
        # Get switch type and determine device_type parameter
        switch_type = self.view.get_switch_type()
        device_type = 'catalyst_3850' if switch_type == "3850" else 'catalyst_2960'

        # Get unified conversion module
        convert_module = self.modules[ScriptType.CONVERT]

        # Clear console
        self.view.clear_console()

        # Process based on source type
        if source_type == "ip":
            # IP source
            self._handle_ip_source(convert_module, api_key, meraki_serials, device_type)
        else:
            # File source
            self._handle_file_source(convert_module, api_key, meraki_serials, device_type)
    
    def _handle_ip_source(self, convert_module, api_key, meraki_serials, device_type):
        """
        Handle IP-based conversion.

        Args:
            convert_module: The conversion module to use
            api_key (str): The Meraki API key
            meraki_serials (list): List of Meraki serials
            device_type (str): Device type ('catalyst_2960' or 'catalyst_3850')
        """
        catalyst_ip = self.view.get_ip_address()
        if not catalyst_ip:
            messagebox.showerror("Error", "Catalyst switch IP is required.")
            return

        # Get credentials
        credentials = self._get_credentials()
        if not credentials:
            return

        # Start task
        self.view.append_console(f"Connecting to Catalyst switch at {catalyst_ip}...\n")
        self.view.append_console(f"Device type: {device_type}\n")

        def run_conversion():
            # Run the conversion with credentials passed as parameter
            convert_module.run(
                meraki_api_key=api_key,
                meraki_cloud_ids=meraki_serials,
                catalyst_ip=catalyst_ip,
                device_type=device_type,
                credentials_list=credentials
            )
            return None  # No specific result to return

        # Run in background
        BackgroundTask.run(
            run_conversion,
            console_widget=self.view.console,
            success_callback=lambda result: self.view.append_console("\nConfiguration conversion completed.\n"),
            error_callback=self._handle_error
        )
    
    def _handle_file_source(self, convert_module, api_key, meraki_serials, device_type):
        """
        Handle file-based conversion.

        Args:
            convert_module: The conversion module to use
            api_key (str): The Meraki API key
            meraki_serials (list): List of Meraki serials
            device_type (str): Device type ('catalyst_2960' or 'catalyst_3850')
        """
        config_file = self.view.get_config_file_path()
        hostname = self.view.get_hostname()

        if not config_file:
            messagebox.showerror("Error", "Configuration file path is required.")
            return

        if not hostname:
            messagebox.showerror("Error", "Switch hostname is required.")
            return

        # Read config file
        try:
            with open(config_file, 'r') as file:
                catalyst_config = file.read()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read configuration file: {str(e)}")
            return

        # Start task
        self.view.append_console(f"Converting configuration for {hostname}...\n")
        self.view.append_console(f"Device type: {device_type}\n")

        def run_conversion():
            # Run the conversion with device_type parameter
            convert_module.run(
                meraki_api_key=api_key,
                meraki_cloud_ids=meraki_serials,
                catalyst_config=catalyst_config,
                device_type=device_type
            )
            return None  # No specific result to return

        # Run in background
        BackgroundTask.run(
            run_conversion,
            console_widget=self.view.console,
            success_callback=lambda result: self.view.append_console("\nConfiguration conversion completed.\n"),
            error_callback=self._handle_error
        )
    
    def _get_credentials(self):
        """
        Get credentials for switch access.
        
        Returns:
            list or None: List of credential dictionaries or None if cancelled
        """
        creds_count = self.credentials_model.get_credentials_count()
        
        if creds_count == 0:
            # No saved credentials, prompt for new ones
            dialog = CredentialSelector(self.view.parent, self.credentials_model.get_credentials())
            self.view.parent.wait_window(dialog)
            
            if not dialog.result:
                return None
            
            # Convert to format expected by scripts
            return [{
                'username': dialog.result['username'],
                'password': dialog.result['password']
            }]
        elif creds_count == 1:
            # Only one credential, use it directly
            cred = self.credentials_model.get_credentials()[0]
            return [{'username': cred['username'], 'password': cred['password']}]
        else:
            # Multiple credentials, let user select
            dialog = CredentialSelector(self.view.parent, self.credentials_model.get_credentials())
            self.view.parent.wait_window(dialog)
            
            if not dialog.result:
                return None
            
            # Convert to format expected by scripts
            return [{
                'username': dialog.result['username'],
                'password': dialog.result['password']
            }]
    
    def manage_credentials(self):
        """Open dialog to manage switch credentials."""
        from views.dialogs.credential_dialog import CredentialListManager
        
        dialog = CredentialListManager(self.view.parent, self.credentials_model.get_credentials())
        self.view.parent.wait_window(dialog)
        
        if dialog.result is not None:
            # Clear existing credentials
            self.credentials_model.clear_credentials()
            
            # Add each credential
            for cred in dialog.result:
                self.credentials_model.add_credential(cred)
    
    def manage_serials(self):
        """Open dialog to manage Meraki serial numbers."""
        dialog = SerialListManager(
            self.view.parent,
            self.serials_model.get_serials("convert"),
            "Manage Meraki Serial Numbers (Convert)"
        )
        self.view.parent.wait_window(dialog)
        
        if dialog.result is not None:
            self.serials_model.set_serials("convert", dialog.result)
    
    def browse_config_file(self):
        """Open file dialog to select a config file."""
        self.view.show_file_dialog()
    
    def _handle_error(self, error):
        """
        Handle errors during conversion.
        
        Args:
            error: The exception that occurred
        """
        error_message = f"Error during conversion: {str(error)}"
        
        # Log the error details to the console
        self.view.append_console(f"\n{error_message}\n")
        traceback.print_exc(file=self.view.console)
        
        # Show error message
        messagebox.showerror("Error", error_message)