"""
Controller for the comparison functionality.
"""

import os
import traceback
from tkinter import messagebox

from utils.workers import BackgroundTask
from config.script_types import ScriptType


class ComparisonController:
    """
    Controller for the Catalyst/Meraki comparison functionality.

    This controller provides access to models and comparison modules.
    The ComparisonWizard handles most of the comparison flow internally.
    """

    def __init__(self, credentials_model, serials_model, switch_data_model, modules):
        """
        Initialize the comparison controller.

        Args:
            credentials_model: The credentials model
            serials_model: The serials model
            switch_data_model: The switch data model for saved captures
            modules: Dictionary of loaded script modules
        """
        self.credentials_model = credentials_model
        self.serials_model = serials_model
        self.switch_data_model = switch_data_model
        self.modules = modules

    def get_interface_module(self):
        """Get the interface comparison module."""
        return self.modules.get(ScriptType.COMPARE_INTERFACES)

    def get_mac_module(self):
        """Get the MAC comparison module."""
        return self.modules.get(ScriptType.COMPARE_MAC)

    def run_interface_comparison(self, api_key, meraki_serials, catalyst_data,
                                  hostname, console_widget=None):
        """
        Run interface comparison.

        Args:
            api_key: Meraki API key
            meraki_serials: List of Meraki serial numbers
            catalyst_data: Captured Catalyst interface data
            hostname: Switch hostname
            console_widget: Optional console widget for output

        Returns:
            Comparison results or None on error
        """
        compare_module = self.get_interface_module()
        if not compare_module:
            messagebox.showerror("Error", "Interface comparison module not loaded.")
            return None

        def do_comparison():
            results, _ = compare_module.run(
                meraki_api_key=api_key,
                meraki_cloud_ids=meraki_serials,
                catalyst_ip=None,
                catalyst_interfaces=catalyst_data,
                name=hostname,
                credentials_list=None
            )
            return results

        return do_comparison()

    def run_mac_comparison(self, api_key, meraki_serials, catalyst_data,
                           hostname, console_widget=None):
        """
        Run MAC address comparison.

        Args:
            api_key: Meraki API key
            meraki_serials: List of Meraki serial numbers
            catalyst_data: Captured Catalyst MAC data
            hostname: Switch hostname
            console_widget: Optional console widget for output

        Returns:
            Comparison results or None on error
        """
        compare_module = self.get_mac_module()
        if not compare_module:
            messagebox.showerror("Error", "MAC comparison module not loaded.")
            return None

        def do_comparison():
            results, _ = compare_module.run(
                meraki_api_key=api_key,
                meraki_cloud_ids=meraki_serials,
                catalyst_ip=None,
                catalyst_macs=catalyst_data,
                name=hostname,
                credentials_list=None
            )
            return results

        return do_comparison()

    def get_saved_interface_captures(self):
        """Get list of saved interface captures."""
        return self.switch_data_model.get_saved_interface_captures()

    def get_saved_mac_captures(self):
        """Get list of saved MAC captures."""
        return self.switch_data_model.get_saved_mac_captures()

    def load_capture_data(self, filename):
        """
        Load saved capture data from file.

        Args:
            filename: The capture filename

        Returns:
            DataFrame or None
        """
        return self.switch_data_model.load_data_from_file(filename)
