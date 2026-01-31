"""
Controller for the conversion/migration functionality.
"""

import os
import traceback
from tkinter import messagebox

from utils.workers import BackgroundTask
from config.script_types import ScriptType


class ConversionController:
    """
    Controller for the Catalyst to Meraki migration functionality.

    This controller handles running conversions based on data collected
    from the ConversionWizard.
    """

    def __init__(self, credentials_model, serials_model, modules):
        """
        Initialize the conversion controller.

        Args:
            credentials_model: The credentials model
            serials_model: The serials model
            modules: Dictionary of loaded script modules
        """
        self.credentials_model = credentials_model
        self.serials_model = serials_model
        self.modules = modules

    def run_conversion(self, wizard_data, console_widget=None):
        """
        Run the conversion process using data from the wizard.

        Args:
            wizard_data (dict): Data collected from the ConversionWizard:
                - source_type: 'ip' or 'file'
                - catalyst_ip: IP address (for IP source)
                - config_file_path: Path to config file (for file source)
                - hostname: Switch hostname (for file source)
                - credentials: Credential dict with username/password
                - meraki_serials: List of Meraki serial numbers
                - switch_type: '2960' or '3850'
            console_widget: Optional widget to display output
        """
        # Check if API key is set
        api_key = os.getenv("MERAKI_API_KEY") or os.getenv("MERAKI_DASHBOARD_API_KEY")
        if not api_key:
            messagebox.showerror("Error", "Meraki API Key is not set. "
                               "Please set it in the Settings.")
            return

        # Get data from wizard
        source_type = wizard_data.get('source_type', 'ip')
        meraki_serials = wizard_data.get('meraki_serials', [])
        switch_type = wizard_data.get('switch_type', '2960')

        if not meraki_serials:
            messagebox.showerror("Error", "Meraki serial numbers are required.")
            return

        # Determine device_type parameter
        device_type = 'catalyst_3850' if switch_type == '3850' else 'catalyst_2960'

        # Get unified conversion module
        convert_module = self.modules.get(ScriptType.CONVERT)
        if not convert_module:
            messagebox.showerror("Error", "Conversion module not loaded.")
            return

        # Clear console if provided
        if console_widget:
            console_widget.delete('1.0', 'end')

        # Process based on source type
        if source_type == 'ip':
            self._run_ip_conversion(
                convert_module, api_key, wizard_data,
                meraki_serials, device_type, console_widget
            )
        else:
            self._run_file_conversion(
                convert_module, api_key, wizard_data,
                meraki_serials, device_type, console_widget
            )

    def _run_ip_conversion(self, convert_module, api_key, wizard_data,
                           meraki_serials, device_type, console_widget):
        """
        Run IP-based conversion.

        Args:
            convert_module: The conversion module
            api_key: Meraki API key
            wizard_data: Data from wizard
            meraki_serials: List of Meraki serials
            device_type: Device type string
            console_widget: Console widget for output
        """
        catalyst_ip = wizard_data.get('catalyst_ip', '')
        credentials = wizard_data.get('credentials', {})

        if not catalyst_ip:
            messagebox.showerror("Error", "Catalyst switch IP is required.")
            return

        if not credentials:
            messagebox.showerror("Error", "Credentials are required.")
            return

        # Format credentials for the script
        credentials_list = [{
            'username': credentials.get('username', ''),
            'password': credentials.get('password', '')
        }]

        # Log to console
        self._append_console(console_widget,
                            f"Connecting to Catalyst switch at {catalyst_ip}...\n")
        self._append_console(console_widget, f"Device type: {device_type}\n")

        def run_conversion():
            convert_module.run(
                meraki_api_key=api_key,
                meraki_cloud_ids=meraki_serials,
                catalyst_ip=catalyst_ip,
                device_type=device_type,
                credentials_list=credentials_list
            )
            return None

        # Run in background
        BackgroundTask.run(
            run_conversion,
            console_widget=console_widget,
            success_callback=lambda r: self._on_success(console_widget),
            error_callback=lambda e: self._on_error(e, console_widget)
        )

    def _run_file_conversion(self, convert_module, api_key, wizard_data,
                             meraki_serials, device_type, console_widget):
        """
        Run file-based conversion.

        Args:
            convert_module: The conversion module
            api_key: Meraki API key
            wizard_data: Data from wizard
            meraki_serials: List of Meraki serials
            device_type: Device type string
            console_widget: Console widget for output
        """
        config_file = wizard_data.get('config_file_path', '')
        hostname = wizard_data.get('hostname', '')

        if not config_file:
            messagebox.showerror("Error", "Configuration file path is required.")
            return

        if not hostname:
            messagebox.showerror("Error", "Switch hostname is required.")
            return

        # Read config file
        try:
            with open(config_file, 'r') as f:
                catalyst_config = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read configuration file: {str(e)}")
            return

        # Log to console
        self._append_console(console_widget,
                            f"Converting configuration for {hostname}...\n")
        self._append_console(console_widget, f"Device type: {device_type}\n")

        def run_conversion():
            convert_module.run(
                meraki_api_key=api_key,
                meraki_cloud_ids=meraki_serials,
                catalyst_config=catalyst_config,
                device_type=device_type
            )
            return None

        # Run in background
        BackgroundTask.run(
            run_conversion,
            console_widget=console_widget,
            success_callback=lambda r: self._on_success(console_widget),
            error_callback=lambda e: self._on_error(e, console_widget)
        )

    def _append_console(self, console_widget, text):
        """Append text to console widget."""
        if console_widget:
            console_widget.insert('end', text)
            console_widget.see('end')

    def _on_success(self, console_widget):
        """Handle successful conversion."""
        self._append_console(console_widget,
                            "\nConfiguration conversion completed.\n")

    def _on_error(self, error, console_widget):
        """Handle conversion error."""
        error_message = f"Error during conversion: {str(error)}"
        self._append_console(console_widget, f"\n{error_message}\n")

        # Print traceback to console
        if console_widget:
            import io
            tb_io = io.StringIO()
            traceback.print_exc(file=tb_io)
            self._append_console(console_widget, tb_io.getvalue())

        messagebox.showerror("Error", error_message)
