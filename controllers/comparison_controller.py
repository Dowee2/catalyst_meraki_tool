"""
Controller for the comparison tabs functionality.
"""

import os
import traceback
from tkinter import messagebox

from views.dialogs.credential_dialog import CredentialListManager
from views.dialogs.credential_dialog import CredentialSelector
from views.dialogs.serial_dialog import SerialListManager
from views.dialogs.credential_dialog import CredentialDialog
from utils.workers import BackgroundTask
from config.script_types import ScriptType

class ComparisonController:
    """
    Controller for the Interface Comparison and MAC Address Comparison tabs functionality.
    """
    
    def __init__(self, interface_view, mac_view, credentials_model, serials_model, switch_data_model, modules):
        """Initialize with switch_data_model added."""
        self.interface_view = interface_view
        self.mac_view = mac_view
        self.credentials_model = credentials_model
        self.serials_model = serials_model
        self.switch_data_model = switch_data_model  # New model
        self.modules = modules
        
        # Set up callbacks
        self._setup_callbacks()
        
        # Set up model observers
        self._setup_observers()
        
        # Update UI with initial data
        self._update_interface_serials_display()
        self._update_mac_serials_display()
        self._update_capture_lists()
    
    def _setup_callbacks(self):
        """Set up UI callbacks."""
        # Interface tab callbacks
        self.interface_view.set_callback("capture_interfaces", self.capture_interface_status)
        self.interface_view.set_callback("start_comparison", self.start_interface_comparison)
        self.interface_view.set_callback("manage_credentials", self.manage_credentials)
        self.interface_view.set_callback("manage_serials", self.manage_interface_serials)
        
        # MAC tab callbacks
        self.mac_view.set_callback("capture_macs", self.capture_mac_addresses)
        self.mac_view.set_callback("start_comparison", self.start_mac_comparison)
        self.mac_view.set_callback("manage_credentials", self.manage_credentials)
        self.mac_view.set_callback("manage_serials", self.manage_mac_serials)
    
        # Set up additional observers
        self.switch_data_model.add_observer(self._update_capture_lists)
        
    
    def _update_capture_lists(self):
        """Update the capture dropdown lists."""
        try:
            # Update interface captures list
            interface_captures = self.switch_data_model.get_saved_interface_captures()
            interface_options = [f"{c['hostname']} ({c['switch_ip']}) - {c['datetime']} ({c['count']} interfaces)" 
                                for c in interface_captures]
            self.interface_view.set_capture_options(interface_options, interface_captures)
            
            # Update MAC captures list
            mac_captures = self.switch_data_model.get_saved_mac_captures()
            mac_options = [f"{c['hostname']} ({c['switch_ip']}) - {c['datetime']} ({c['count']} MAC entries)" 
                        for c in mac_captures]
            self.mac_view.set_capture_options(mac_options, mac_captures)
        
        except Exception as e:
            print(f"Error updating capture lists: {e}")
            traceback.print_exc()
        

    def capture_interface_status(self):
        """Capture interface status from a Catalyst switch."""
        # Get IP address
        catalyst_ip = self.interface_view.get_ip_address()
        if not catalyst_ip:
            messagebox.showerror("Error", "Catalyst switch IP is required.")
            return
        
        # Get credentials
        credentials = self._get_credentials()
        if not credentials:
            return
        
        # Get interface comparison module using ScriptType enum
        compare_module = self.modules[ScriptType.COMPARE_INTERFACES]

        # Clear console
        self.interface_view.clear_console()

        # Start task
        self.interface_view.append_console(f"Connecting to Catalyst switch at {catalyst_ip}...\n")
        print("About to start interface capture")
        self.interface_view.append_console("Starting interface capture task...\n")

        def run_capture():
            # Import get_running_config to capture interface data directly
            from utils.netmiko_utils import get_running_config
            from config.constants import DEFAULT_READ_TIMEOUT

            # Get interface status using get_running_config
            interface_data, switch_name = get_running_config(
                ip_address=catalyst_ip,
                credentials=credentials,
                command='show ip int brief',
                use_textfsm=True,
                read_timeout=DEFAULT_READ_TIMEOUT
            )

            # Save data
            filepath = self.switch_data_model.save_interface_data(catalyst_ip, switch_name, interface_data)

            return {"switch_name": switch_name, "count": len(interface_data), "filepath": filepath}
        
        # Run in background
        BackgroundTask.run(
            run_capture,
            console_widget=self.interface_view.console,
            success_callback=self._handle_interface_capture_success,
            error_callback=self._handle_interface_capture_error
        )

    def _handle_interface_capture_success(self, result):
        """Handle successful interface capture."""
        switch_name = result["switch_name"]
        count = result["count"]
        filepath = result["filepath"]
        
        # Display success message
        self.interface_view.append_console(
            f"\nSuccessfully captured {count} interfaces from {switch_name}.\n"
            f"Data saved to: {filepath}\n\n"
            f"You can now select 'Compare with Meraki Switches' to compare this data with Meraki switches.\n"
        )
        
        # Update the capture dropdown
        self._update_capture_lists()
        
        # Switch to compare mode
        self.interface_view.set_mode("capture")

    def _handle_interface_capture_error(self, error):
        """Handle errors during interface capture."""
        error_message = f"Error capturing interface status: {str(error)}"
        
        # Log the error details to the console
        self.interface_view.append_console(f"\n{error_message}\n")
        traceback.print_exc(file=self.interface_view.console)
        
        # Show error message
        messagebox.showerror("Error", error_message)
        
    def capture_mac_addresses(self):
        """Capture MAC address table from a Catalyst switch."""
        # Get IP address
        catalyst_ip = self.mac_view.get_ip_address()
        if not catalyst_ip:
            messagebox.showerror("Error", "Catalyst switch IP is required.")
            return
        
        # Get credentials
        credentials = self._get_credentials()
        if not credentials:
            return
        
        # Get MAC comparison module using ScriptType enum
        compare_module = self.modules[ScriptType.COMPARE_MAC]

        # Clear console
        self.mac_view.clear_console()

        # Start task
        self.mac_view.append_console(f"Connecting to Catalyst switch at {catalyst_ip}...\n")

        def run_capture():
            # Import get_running_config to capture MAC data directly
            import pandas as pd
            from utils.netmiko_utils import get_running_config
            from config.constants import UPLINK_PORT_THRESHOLD

            # Get MAC address table using get_running_config
            macs_raw, switch_name = get_running_config(
                ip_address=catalyst_ip,
                credentials=credentials,
                command='show mac address-table',
                use_textfsm=True,
                read_timeout=90
            )

            # Convert to DataFrame and process (same logic as in compare_mac_address_table.py)
            macs_df = pd.DataFrame(macs_raw)
            macs_df.rename(columns={'destination_address': 'mac_address', 'destination_port': 'port', 'vlan_id': 'vlan'}, inplace=True)
            macs_df['port'] = macs_df['port'].apply(lambda x: x[0])
            macs_df = macs_df[['mac_address', 'vlan', 'port']]

            # Save data
            filepath = self.switch_data_model.save_mac_data(catalyst_ip, switch_name, macs_df)

            return {"switch_name": switch_name, "count": len(macs_df), "filepath": filepath}
        
        # Run in background
        BackgroundTask.run(
            run_capture,
            console_widget=self.mac_view.console,
            success_callback=self._handle_mac_capture_success,
            error_callback=self._handle_mac_capture_error
        )

    def _handle_mac_capture_success(self, result):
        """Handle successful MAC address capture."""
        switch_name = result["switch_name"]
        count = result["count"]
        filepath = result["filepath"]
        
        # Display success message
        self.mac_view.append_console(
            f"\nSuccessfully captured {count} MAC addresses from {switch_name}.\n"
            f"Data saved to: {filepath}\n\n"
            f"You can now select 'Compare with Meraki Switches' to compare this data with Meraki switches.\n"
        )
        
        # Update the capture dropdown
        self._update_capture_lists()
        
        # Switch to compare mode
        self.mac_view._toggle_mode()

    def _handle_mac_capture_error(self, error):
        """Handle errors during MAC address capture."""
        error_message = f"Error capturing MAC address table: {str(error)}"
        
        # Log the error details to the console
        self.mac_view.append_console(f"\n{error_message}\n")
        traceback.print_exc(file=self.mac_view.console)
        
        # Show error message
        messagebox.showerror("Error", error_message)
    
    def _setup_observers(self):
        """Set up model change observers."""
        # Observe serials model for both contexts
        self.serials_model.add_observer("interface", self._update_interface_serials_display)
        self.serials_model.add_observer("mac", self._update_mac_serials_display)
    
    def _update_interface_serials_display(self):
        """Update the interface serials display from the model."""
        serials = self.serials_model.get_serials("interface")
        self.interface_view.set_serials_display(serials)
    
    def _update_mac_serials_display(self):
        """Update the MAC serials display from the model."""
        serials = self.serials_model.get_serials("mac")
        self.mac_view.set_serials_display(serials)
        
    def start_interface_comparison(self):
        """Start the interface comparison process."""
        # Check if API key is set
        api_key = os.getenv("MERAKI_API_KEY")
        if not api_key:
            messagebox.showerror("Error", "Meraki API Key is not set. Please set it in the Settings tab.")
            return
        
        # Get Meraki serials
        meraki_serials = self.serials_model.get_serials("interface")
        if not meraki_serials:
            messagebox.showerror("Error", "Meraki serial numbers are required.")
            return
        
        # Get selected capture data
        current_index = self.interface_view.capture_combo.current()
        if current_index < 0 or current_index >= len(self.interface_view.captures_data):
            messagebox.showerror("Error", "Please select a valid captured data set.")
            return
            
        selected_capture = self.interface_view.captures_data[current_index]
        
        # Load the saved interface data
        saved_data = self.switch_data_model.load_data_from_file(selected_capture['filename'])
        if saved_data is None:
            messagebox.showerror("Error", f"Could not load saved data file: {selected_capture['filename']}")
            return
        
        # Clear console and results
        self.interface_view.clear_console()
        self.interface_view.clear_results()
        
        # Start task
        hostname = selected_capture.get('hostname', 'Unknown')
        self.interface_view.append_console(f"Comparing saved interfaces from {hostname} with Meraki switches...\n")
        
        def run_comparison():
            # Run the comparison with pre-loaded Catalyst data using ScriptType enum
            compare_module = self.modules[ScriptType.COMPARE_INTERFACES]
            comparison_results, _ = compare_module.run(
                meraki_api_key=api_key,
                meraki_cloud_ids=meraki_serials,
                catalyst_ip=None,  # No IP needed since we're using saved data
                catalyst_interfaces=saved_data.to_dict('records'),  # Convert DataFrame to list of dicts
                name=hostname,
                credentials_list=None  # No credentials needed for saved data
            )
            return {"results": comparison_results, "switch_name": hostname}
        
        # Run in background
        BackgroundTask.run(
            run_comparison,
            console_widget=self.interface_view.console,
            success_callback=self._handle_interface_success,
            error_callback=self._handle_interface_error
        )
    
    def _handle_interface_success(self, result):
        """
        Handle successful interface comparison.
        
        Args:
            result (dict): Dictionary containing results and switch name
        """
        comparison_results = result["results"]
        switch_name = result["switch_name"]
        
        # Display results
        self.interface_view.append_console(f"\nComparison completed for {switch_name}.\n")
        self.interface_view.set_results(comparison_results)
    
    def _handle_interface_error(self, error):
        """
        Handle errors during interface comparison.
        
        Args:
            error: The exception that occurred
        """
        error_message = f"Error during interface comparison: {str(error)}"
        
        # Log the error details to the console
        self.interface_view.append_console(f"\n{error_message}\n")
        traceback.print_exc(file=self.interface_view.console)
        
        # Show error message
        messagebox.showerror("Error", error_message)
        
        
    def start_mac_comparison(self):
        """Start the MAC address comparison process."""
        # Check if API key is set
        api_key = os.getenv("MERAKI_API_KEY")
        if not api_key:
            messagebox.showerror("Error", "Meraki API Key is not set. Please set it in the Settings tab.")
            return
        
        # Get Meraki serials
        meraki_serials = self.serials_model.get_serials("mac")
        if not meraki_serials:
            messagebox.showerror("Error", "Meraki serial numbers are required.")
            return
        
        # Get selected capture data
        current_index = self.mac_view.capture_combo.current()
        if current_index < 0 or current_index >= len(self.mac_view.captures_data):
            messagebox.showerror("Error", "Please select a valid captured data set.")
            return
            
        selected_capture = self.mac_view.captures_data[current_index]
        
        # Load the saved MAC address data
        saved_data = self.switch_data_model.load_data_from_file(selected_capture['filename'])
        if saved_data is None:
            messagebox.showerror("Error", f"Could not load saved data file: {selected_capture['filename']}")
            return
        
        # Clear console and results
        self.mac_view.clear_console()
        self.mac_view.clear_results()
        
        # Start task
        hostname = selected_capture.get('hostname', 'Unknown')
        self.mac_view.append_console(f"Comparing saved MAC addresses from {hostname} with Meraki switches...\n")
        
        def run_comparison():
            # Run the comparison with pre-loaded Catalyst data using ScriptType enum
            compare_module = self.modules[ScriptType.COMPARE_MAC]
            comparison_results, _ = compare_module.run(
                meraki_api_key=api_key,
                meraki_cloud_ids=meraki_serials,
                catalyst_ip=None,  # No IP needed since we're using saved data
                catalyst_macs=saved_data.to_dict('records'),  # Convert DataFrame to list of dicts
                name=hostname,
                credentials_list=None  # No credentials needed for saved data
            )
            return {"results": comparison_results, "switch_name": hostname}
        
        # Run in background
        BackgroundTask.run(
            run_comparison,
            console_widget=self.mac_view.console,
            success_callback=self._handle_mac_success,
            error_callback=self._handle_mac_error
        )
    
    def _handle_mac_success(self, result):
        """
        Handle successful MAC address comparison.
        
        Args:
            result (dict): Dictionary containing results and switch name
        """
        comparison_results = result["results"]
        switch_name = result["switch_name"]
        
        # Display results
        self.mac_view.append_console(f"\nComparison completed for {switch_name}.\n")
        self.mac_view.set_results(comparison_results)
    
    def _handle_mac_error(self, error):
        """
        Handle errors during MAC address comparison.
        
        Args:
            error: The exception that occurred
        """
        error_message = f"Error during MAC address comparison: {str(error)}"
        
        # Log the error details to the console
        self.mac_view.append_console(f"\n{error_message}\n")
        traceback.print_exc(file=self.mac_view.console)
        
        # Show error message
        messagebox.showerror("Error", error_message)
    
    def _get_credentials(self):
        """
        Get credentials for switch access.
        
        Returns:
            list or None: List of credential dictionaries or None if cancelled
        """
        creds_count = self.credentials_model.get_credentials_count()
        
        if creds_count == 0:
            # No saved credentials, prompt for new ones
            dialog = CredentialDialog(self.interface_view.parent)
            self.interface_view.parent.wait_window(dialog)
            
            if not dialog.result:
                return None
            
            # Ask if user wants to save the credentials
            if messagebox.askyesno("Save Credentials", 
                                   "Do you want to save these credentials for future use?"):
                self.credentials_model.add_credential(dialog.result)
            
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
            dialog = CredentialSelector(self.interface_view.parent, self.credentials_model.get_credentials())
            self.interface_view.parent.wait_window(dialog)
            
            if not dialog.result:
                return None
            
            # Convert to format expected by scripts
            return [{
                'username': dialog.result['username'],
                'password': dialog.result['password']
            }]
    
    def manage_credentials(self):
        """Open dialog to manage switch credentials."""
        
        dialog = CredentialListManager(self.interface_view.parent, self.credentials_model.get_credentials())
        self.interface_view.parent.wait_window(dialog)
        
        if dialog.result is not None:
            # Clear existing credentials
            self.credentials_model.clear_credentials()
            
            # Add each credential
            for cred in dialog.result:
                self.credentials_model.add_credential(cred)
    
    def manage_interface_serials(self):
        """Open dialog to manage interface comparison serials."""
        dialog = SerialListManager(
            self.interface_view.parent,
            self.serials_model.get_serials("interface"),
            "Manage Meraki Serial Numbers (Interface Comparison)"
        )
        self.interface_view.parent.wait_window(dialog)
        
        if dialog.result is not None:
            self.serials_model.set_serials("interface", dialog.result)
    
    def manage_mac_serials(self):
        """Open dialog to manage MAC comparison serials."""
        dialog = SerialListManager(
            self.mac_view.parent,
            self.serials_model.get_serials("mac"),
            "Manage Meraki Serial Numbers (MAC Comparison)"
        )
        self.mac_view.parent.wait_window(dialog)
        
        if dialog.result is not None:
            self.serials_model.set_serials("mac", dialog.result)