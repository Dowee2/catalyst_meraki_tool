"""
IP address input component with validation.
"""

import re
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from config.theme import Colors, Fonts, Spacing


class IPInput(ttk.Frame):
    """
    An IP address input field with real-time validation.

    Features:
    - Label and input field
    - Example text placeholder
    - Real-time validation with visual feedback
    - Validation callback
    """

    # IP address validation pattern
    IP_PATTERN = re.compile(
        r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    )

    def __init__(
        self,
        parent,
        label: str = "IP Address",
        placeholder: str = "192.168.1.1",
        on_change: Optional[Callable[[str, bool], None]] = None,
        **kwargs
    ):
        """
        Initialize an IP input field.

        Args:
            parent: Parent widget
            label: Label text above the input
            placeholder: Example text shown when empty
            on_change: Callback(ip_value, is_valid) when input changes
        """
        super().__init__(parent, **kwargs)
        self.label_text = label
        self.placeholder_text = placeholder
        self.on_change = on_change
        self._is_valid = False

        self._create_ui()

    def _create_ui(self):
        """Create the IP input UI."""
        # Label
        label = ttk.Label(
            self,
            text=self.label_text,
            font=Fonts.NORMAL
        )
        label.pack(anchor=tk.W)

        # Input container
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, pady=(Spacing.XS, 0))

        # Entry field
        self.ip_var = tk.StringVar()
        self.ip_var.trace_add('write', self._on_input_change)

        self.entry = ttk.Entry(
            input_frame,
            textvariable=self.ip_var,
            font=Fonts.NORMAL,
            width=20
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Validation indicator
        self.indicator = ttk.Label(
            input_frame,
            text="",
            font=('Segoe UI', 12)
        )
        self.indicator.pack(side=tk.LEFT, padx=(Spacing.SM, 0))

        # Example/help text
        self.example_label = ttk.Label(
            self,
            text=f"Example: {self.placeholder_text}",
            font=Fonts.SMALL,
            foreground=Colors.TEXT_SECONDARY
        )
        self.example_label.pack(anchor=tk.W, pady=(Spacing.XS, 0))

        # Error message (hidden by default)
        self.error_label = ttk.Label(
            self,
            text="",
            font=Fonts.SMALL,
            foreground=Colors.ERROR
        )
        self.error_label.pack(anchor=tk.W)

    def _on_input_change(self, *args):
        """Handle input changes and validate."""
        value = self.ip_var.get().strip()

        if not value:
            # Empty - neutral state
            self._is_valid = False
            self.indicator.config(text="")
            self.error_label.config(text="")
        elif self._validate_ip(value):
            # Valid IP
            self._is_valid = True
            self.indicator.config(text="\u2714", foreground=Colors.SUCCESS)
            self.error_label.config(text="")
        else:
            # Invalid IP
            self._is_valid = False
            self.indicator.config(text="\u2716", foreground=Colors.ERROR)
            # Show error only if it looks like a complete attempt
            if len(value) > 6:
                self.error_label.config(text="Please enter a valid IP address")
            else:
                self.error_label.config(text="")

        # Call change callback
        if self.on_change:
            self.on_change(value, self._is_valid)

    def _validate_ip(self, ip: str) -> bool:
        """
        Validate an IP address.

        Args:
            ip: The IP address string

        Returns:
            True if valid, False otherwise
        """
        return bool(self.IP_PATTERN.match(ip))

    def get_value(self) -> str:
        """Get the current IP address value."""
        return self.ip_var.get().strip()

    def set_value(self, value: str):
        """Set the IP address value."""
        self.ip_var.set(value)

    def is_valid(self) -> bool:
        """Check if the current value is a valid IP address."""
        return self._is_valid

    def validate(self) -> tuple[bool, str]:
        """
        Validate and return result with message.

        Returns:
            Tuple of (is_valid, error_message)
        """
        value = self.get_value()
        if not value:
            return False, "IP address is required"
        if not self._is_valid:
            return False, "Please enter a valid IP address"
        return True, ""

    def focus(self):
        """Set focus to the entry field."""
        self.entry.focus_set()

    def set_error(self, message: str):
        """Display an error message."""
        self.error_label.config(text=message)
        self.indicator.config(text="\u2716", foreground=Colors.ERROR)

    def clear_error(self):
        """Clear the error message."""
        self.error_label.config(text="")
        if self._is_valid:
            self.indicator.config(text="\u2714", foreground=Colors.SUCCESS)
        else:
            self.indicator.config(text="")
