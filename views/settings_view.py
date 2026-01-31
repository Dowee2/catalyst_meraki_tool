"""
View for the application settings.
"""

import tkinter as tk
from tkinter import ttk

from config.theme import Fonts, Spacing

class SettingsView:
    """
    View for managing application settings.
    """
    
    def __init__(self, parent_frame):
        """
        Initialize the settings view.
        
        Args:
            parent_frame: The parent frame to place UI elements in
        """
        self.parent = parent_frame
        self.callbacks = {}
        
        # Main container
        settings_frame = ttk.Frame(self.parent, padding=Spacing.MD)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # API Key section
        self._create_api_key_section(settings_frame)
        
        # Credentials section
        self._create_credentials_section(settings_frame)
        
        # About section
        self._create_about_section(settings_frame)
    
    def _create_api_key_section(self, parent):
        """
        Create the API key section.
        
        Args:
            parent: The parent frame
        """
        api_frame = ttk.LabelFrame(parent, text="Meraki API Settings")
        api_frame.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD)

        ttk.Label(api_frame, text="API Key:").grid(
            row=0, column=0, padx=Spacing.SM, pady=Spacing.SM, sticky=tk.W)
        self.api_key = ttk.Entry(api_frame, width=50)
        self.api_key.grid(row=0, column=1, padx=Spacing.SM, pady=Spacing.SM, sticky=tk.W)

        self.save_api_button = ttk.Button(api_frame, text="Save API Key",
                                          style="Primary.TButton")
        self.save_api_button.grid(row=0, column=2, padx=Spacing.SM, pady=Spacing.SM)
    
    def _create_credentials_section(self, parent):
        """
        Create the credentials section.
        
        Args:
            parent: The parent frame
        """
        credentials_frame = ttk.LabelFrame(parent, text="Switch Credentials Management")
        credentials_frame.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD, ipady=Spacing.SM)

        self.manage_cred_button = ttk.Button(credentials_frame, text="Manage Credentials",
                                             style="Secondary.TButton")
        self.manage_cred_button.pack(padx=Spacing.SM, pady=Spacing.SM, anchor=tk.W)

        # Label showing the number of saved credentials
        self.credentials_count_var = tk.StringVar(value="No credentials saved")
        ttk.Label(credentials_frame, textvariable=self.credentials_count_var,
                  style="Secondary.TLabel").pack(padx=Spacing.SM, pady=Spacing.SM, anchor=tk.W)
    
    def _create_about_section(self, parent):
        """
        Create the about section.
        
        Args:
            parent: The parent frame
        """
        about_frame = ttk.LabelFrame(parent, text="About")
        about_frame.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD)

        about_text = """Catalyst to Meraki Migration Tool

This tool helps network administrators migrate configurations from Cisco Catalyst
switches to Cisco Meraki switches. It provides functionality for converting configs
and comparing interface status and MAC address tables between Catalyst and Meraki switches.

Features:
- Convert configuration from Catalyst to Meraki switches
- Compare interface status between Catalyst and Meraki switches
- Compare MAC address tables between Catalyst and Meraki switches
- Support for both direct switch connectivity and config file import
- Enhanced serial number management with ordering control

Version: 1.0
"""
        ttk.Label(about_frame, text=about_text, justify=tk.LEFT,
                  font=Fonts.SMALL, style="Card.TLabel").pack(padx=Spacing.SM, pady=Spacing.SM)
    
    def get_api_key(self):
        """
        Get the entered API key.
        
        Returns:
            str: The API key
        """
        return self.api_key.get().strip()
    
    def set_api_key(self, api_key):
        """
        Set the API key field.
        
        Args:
            api_key (str): The API key
        """
        self.api_key.delete(0, tk.END)
        self.api_key.insert(0, api_key)
    
    def set_credentials_count(self, count):
        """
        Update the credentials count label.
        
        Args:
            count (int): The number of saved credentials
        """
        if count == 0:
            self.credentials_count_var.set("No credentials saved")
        elif count == 1:
            self.credentials_count_var.set("1 credential saved")
        else:
            self.credentials_count_var.set(f"{count} credentials saved")
    
    def set_callback(self, event_name, callback):
        """
        Set a callback function for a UI event.
        
        Args:
            event_name (str): The event name
            callback: The callback function
        """
        self.callbacks[event_name] = callback
        
        # Connect callbacks to UI elements
        if event_name == "save_api_key":
            self.save_api_button.config(command=callback)
        elif event_name == "manage_credentials":
            self.manage_cred_button.config(command=callback)
    
    def on_tab_selected(self):
        """Handle tab selection event."""
        # Update any UI elements as needed when tab is selected
        pass