"""
Main application window for the Catalyst to Meraki Migration Tool.
"""

import tkinter as tk
from tkinter import ttk

from config.theme import apply_theme, Colors, Fonts, Spacing


class MainWindow:
    """
    The main application window with dashboard-based navigation.

    Replaces the old tab-based interface with a wizard-style flow.
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

        # Content container - holds either dashboard or wizards
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Current view tracking
        self.current_view = None
        self.current_view_name = None

        # View references
        self.dashboard = None
        self.conversion_wizard = None
        self.comparison_wizard = None
        self.settings_view = None

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            root, textvariable=self.status_var, relief=tk.SUNKEN,
            anchor=tk.W, padding=(Spacing.SM, Spacing.XS),
            background=Colors.BG_CARD, font=Fonts.SMALL)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, message):
        """
        Set the status bar message.

        Args:
            message (str): The message to display
        """
        self.status_var.set(message)

    def get_content_frame(self):
        """
        Get the content frame for placing views.

        Returns:
            ttk.Frame: The content frame
        """
        return self.content_frame

    def _clear_content(self):
        """Clear the content frame of all widgets."""
        for widget in self.content_frame.winfo_children():
            widget.pack_forget()

    def show_dashboard(self, dashboard_view):
        """
        Show the dashboard view.

        Args:
            dashboard_view: The DashboardView instance
        """
        self._clear_content()
        self.dashboard = dashboard_view
        dashboard_view.pack(in_=self.content_frame, fill=tk.BOTH, expand=True)
        self.current_view = dashboard_view
        self.current_view_name = "dashboard"
        self.set_status("Ready")

    def show_conversion_wizard(self, wizard_view):
        """
        Show the conversion wizard.

        Args:
            wizard_view: The ConversionWizard instance
        """
        self._clear_content()
        self.conversion_wizard = wizard_view
        wizard_view.pack(in_=self.content_frame, fill=tk.BOTH, expand=True)
        self.current_view = wizard_view
        self.current_view_name = "conversion"
        self.set_status("Migration Wizard")

    def show_comparison_wizard(self, wizard_view):
        """
        Show the comparison wizard.

        Args:
            wizard_view: The ComparisonWizard instance
        """
        self._clear_content()
        self.comparison_wizard = wizard_view
        wizard_view.pack(in_=self.content_frame, fill=tk.BOTH, expand=True)
        self.current_view = wizard_view
        self.current_view_name = "comparison"
        self.set_status("Comparison Wizard")

    def show_settings(self, settings_view):
        """
        Show the settings view.

        Args:
            settings_view: The SettingsView instance
        """
        self._clear_content()

        # Create a wrapper with a back button
        wrapper = ttk.Frame(self.content_frame)
        wrapper.pack(fill=tk.BOTH, expand=True)

        # Header with back button
        header_frame = ttk.Frame(wrapper)
        header_frame.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD)

        back_btn = ttk.Button(
            header_frame,
            text="< Back to Dashboard",
            style="Secondary.TButton",
            command=self._on_back_to_dashboard
        )
        back_btn.pack(side=tk.LEFT)

        ttk.Label(
            header_frame,
            text="Settings",
            font=Fonts.HEADER,
            style="Card.TLabel"
        ).pack(side=tk.LEFT, padx=Spacing.LG)

        # Settings content
        self.settings_view = settings_view
        settings_view.pack(in_=wrapper, fill=tk.BOTH, expand=True, padx=Spacing.MD)

        self.current_view = wrapper
        self.current_view_name = "settings"
        self.set_status("Settings")

    def _on_back_to_dashboard(self):
        """Handle back to dashboard button click."""
        if self._back_to_dashboard_callback:
            self._back_to_dashboard_callback()

    def set_back_to_dashboard_callback(self, callback):
        """
        Set the callback for returning to dashboard.

        Args:
            callback: Function to call when back button is clicked
        """
        self._back_to_dashboard_callback = callback

    def get_current_view_name(self):
        """
        Get the name of the current view.

        Returns:
            str: One of "dashboard", "conversion", "comparison", "settings"
        """
        return self.current_view_name
