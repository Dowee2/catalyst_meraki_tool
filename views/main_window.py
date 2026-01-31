"""
Main application window for the Catalyst to Meraki Migration Tool.
"""

import tkinter as tk
from tkinter import ttk

from config.theme import apply_theme, Colors, Fonts, Spacing

class MainWindow:
    """
    The main application window containing the tab navigation and common elements.
    """
    
    def __init__(self, root):
        """
        Initialize the main window.
        
        Args:
            root: The tk root window
        """
        self.root = root
        self.root.title("Catalyst to Meraki Migration Tool")
        
        # Set the window icon if available
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Apply theme
        self.style = apply_theme(root)
        
        # Main container
        self.main_frame = ttk.Frame(root, padding=Spacing.MD)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        # Add workflow explanation at the top
        workflow_frame = ttk.LabelFrame(self.main_frame, text="Workflow")
        workflow_frame.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.SM)

        # Use a more compact format for the workflow text
        workflow_text = ("Migration Flow: 1) Convert Switch Config  2) Move Cables  "
                        "3) Compare Interfaces/MAC Addresses\n"
                        "Note: Comparison functions can be used independently at any time.")
        ttk.Label(workflow_frame, text=workflow_text, font=Fonts.SMALL,
                  style="Card.TLabel").pack(padx=Spacing.MD, pady=Spacing.SM, anchor=tk.W)
        
        # Create tab control - AFTER workflow frame is packed
        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab_convert = ttk.Frame(self.tab_control)
        self.tab_compare_interface = ttk.Frame(self.tab_control)
        self.tab_compare_mac = ttk.Frame(self.tab_control)
        self.tab_settings = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.tab_convert, text="Convert Switch Config")
        self.tab_control.add(self.tab_compare_interface, text="Compare Interfaces")
        self.tab_control.add(self.tab_compare_mac, text="Compare MAC Addresses")
        self.tab_control.add(self.tab_settings, text="Settings")
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            root, textvariable=self.status_var, relief=tk.SUNKEN,
            anchor=tk.W, padding=(Spacing.SM, Spacing.XS),
            background=Colors.BG_CARD, font=Fonts.SMALL)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Register tab change callback
        self.tab_control.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        # Store references to child views
        self.views = {
            "convert": None,
            "interface": None,
            "mac": None,
            "settings": None
        }
        
    def set_status(self, message):
        """
        Set the status bar message.
        
        Args:
            message (str): The message to display
        """
        self.status_var.set(message)
        
    def get_current_tab(self):
        """
        Get the currently selected tab.
        
        Returns:
            str: One of "convert", "interface", "mac", "settings"
        """
        tab_id = self.tab_control.select()
        tab_index = self.tab_control.index(tab_id)
        
        if tab_index == 0:
            return "convert"
        elif tab_index == 1:
            return "interface"
        elif tab_index == 2:
            return "mac"
        else:
            return "settings"
    
    def get_tab_frame(self, tab_name):
        """
        Get the frame for a specific tab.
        
        Args:
            tab_name (str): One of "convert", "interface", "mac", "settings"
            
        Returns:
            ttk.Frame: The requested tab frame
        """
        if tab_name == "convert":
            return self.tab_convert
        elif tab_name == "interface":
            return self.tab_compare_interface
        elif tab_name == "mac":
            return self.tab_compare_mac
        elif tab_name == "settings":
            return self.tab_settings
        else:
            return None
    
    def register_view(self, tab_name, view):
        """
        Register a view for a tab.
        
        Args:
            tab_name (str): The tab name
            view: The view object
        """
        self.views[tab_name] = view
    
    def select_tab(self, tab_name):
        """
        Select a specific tab.
        
        Args:
            tab_name (str): One of "convert", "interface", "mac", "settings"
        """
        if tab_name == "convert":
            self.tab_control.select(0)
        elif tab_name == "interface":
            self.tab_control.select(1)
        elif tab_name == "mac":
            self.tab_control.select(2)
        elif tab_name == "settings":
            self.tab_control.select(3)
    
    def _on_tab_changed(self, event):
        """
        Handle tab change events.
        
        Args:
            event: The tab changed event
        """
        current_tab = self.get_current_tab()
        view = self.views.get(current_tab)
        
        if view and hasattr(view, "on_tab_selected"):
            view.on_tab_selected()