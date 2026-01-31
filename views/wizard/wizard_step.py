"""
Individual wizard step component.
"""

import tkinter as tk
from tkinter import ttk

from config.theme import Colors, Fonts, Spacing


class WizardStep(ttk.Frame):
    """
    A single step in a wizard.

    Contains a title, description, and content area.
    """

    def __init__(self, parent, title, description="", **kwargs):
        """
        Initialize a wizard step.

        Args:
            parent: Parent widget
            title: Step title (displayed as header)
            description: Optional description text
        """
        super().__init__(parent, **kwargs)
        self.title_text = title
        self.description_text = description

        self._create_ui()

    def _create_ui(self):
        """Create the step UI."""
        # Header section
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=Spacing.XL, pady=(Spacing.LG, Spacing.SM))

        # Title
        self.title_label = ttk.Label(
            header_frame,
            text=self.title_text,
            style="Header.TLabel",
            font=Fonts.HEADER)
        self.title_label.pack(anchor=tk.W)

        # Description
        if self.description_text:
            self.desc_label = ttk.Label(
                header_frame,
                text=self.description_text,
                style="Secondary.TLabel",
                wraplength=600)
            self.desc_label.pack(anchor=tk.W, pady=(Spacing.XS, 0))

        # Separator
        separator = ttk.Separator(self, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, padx=Spacing.LG, pady=Spacing.SM)

        # Content area - this is where step-specific widgets go
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(
            fill=tk.BOTH, expand=True,
            padx=Spacing.XL, pady=Spacing.MD)

    def get_content_frame(self):
        """
        Get the content frame for adding step-specific widgets.

        Returns:
            ttk.Frame: The content frame
        """
        return self.content_frame

    def set_title(self, title):
        """Update the step title."""
        self.title_text = title
        self.title_label.config(text=title)

    def set_description(self, description):
        """Update the step description."""
        self.description_text = description
        if hasattr(self, 'desc_label'):
            self.desc_label.config(text=description)
