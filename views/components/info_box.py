"""
Info/help box component for displaying contextual help.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from config.theme import Colors, Fonts, Spacing


class InfoBox(ttk.Frame):
    """
    A styled info/help box for displaying contextual help messages.

    Features:
    - Info, warning, or error styling
    - Icon and message text
    - Optional title
    """

    # Box types with their styling
    TYPES = {
        'info': {
            'bg': '#E0F2FE',           # Light blue
            'border': Colors.PRIMARY,
            'icon': '\u2139',          # Info symbol
            'icon_color': Colors.PRIMARY
        },
        'warning': {
            'bg': Colors.WARNING_BG,
            'border': Colors.WARNING,
            'icon': '\u26A0',          # Warning triangle
            'icon_color': Colors.WARNING
        },
        'error': {
            'bg': Colors.ERROR_BG,
            'border': Colors.ERROR,
            'icon': '\u2716',          # X symbol
            'icon_color': Colors.ERROR
        },
        'success': {
            'bg': Colors.SUCCESS_BG,
            'border': Colors.SUCCESS,
            'icon': '\u2714',          # Checkmark
            'icon_color': Colors.SUCCESS
        },
        'help': {
            'bg': '#F3F4F6',           # Light gray
            'border': Colors.TEXT_SECONDARY,
            'icon': '?',               # Question mark
            'icon_color': Colors.TEXT_SECONDARY
        }
    }

    def __init__(
        self,
        parent,
        message: str,
        title: Optional[str] = None,
        box_type: str = 'info',
        **kwargs
    ):
        """
        Initialize an info box.

        Args:
            parent: Parent widget
            message: The message text to display
            title: Optional title above the message
            box_type: One of 'info', 'warning', 'error', 'success', 'help'
        """
        super().__init__(parent, **kwargs)
        self.message_text = message
        self.title_text = title
        self.box_type = box_type if box_type in self.TYPES else 'info'
        self.type_config = self.TYPES[self.box_type]

        self._create_ui()

    def _create_ui(self):
        """Create the info box UI."""
        # Container with border
        self.container = tk.Frame(
            self,
            bg=self.type_config['bg'],
            highlightthickness=1,
            highlightbackground=self.type_config['border']
        )
        self.container.pack(fill=tk.X, expand=True)

        # Inner padding frame
        inner = tk.Frame(self.container, bg=self.type_config['bg'])
        inner.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.SM)

        # Icon on the left
        icon_label = tk.Label(
            inner,
            text=self.type_config['icon'],
            font=('Segoe UI', 14),
            fg=self.type_config['icon_color'],
            bg=self.type_config['bg']
        )
        icon_label.pack(side=tk.LEFT, padx=(0, Spacing.SM))

        # Text container
        text_frame = tk.Frame(inner, bg=self.type_config['bg'])
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Title (if provided)
        if self.title_text:
            title_label = tk.Label(
                text_frame,
                text=self.title_text,
                font=Fonts.BOLD,
                fg=Colors.TEXT_PRIMARY,
                bg=self.type_config['bg'],
                anchor=tk.W
            )
            title_label.pack(fill=tk.X)

        # Message
        self.message_label = tk.Label(
            text_frame,
            text=self.message_text,
            font=Fonts.NORMAL,
            fg=Colors.TEXT_PRIMARY,
            bg=self.type_config['bg'],
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=500
        )
        self.message_label.pack(fill=tk.X)

    def set_message(self, message: str):
        """Update the message text."""
        self.message_text = message
        self.message_label.configure(text=message)

    def set_type(self, box_type: str):
        """
        Change the box type and restyle.

        Args:
            box_type: One of 'info', 'warning', 'error', 'success', 'help'
        """
        if box_type in self.TYPES:
            self.box_type = box_type
            self.type_config = self.TYPES[box_type]
            # Recreate UI with new style
            for widget in self.winfo_children():
                widget.destroy()
            self._create_ui()
