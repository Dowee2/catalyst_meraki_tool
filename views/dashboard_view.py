"""
Dashboard view - main task selection screen.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from config.theme import Colors, Fonts, Spacing
from views.components.task_card import TaskCard


class DashboardView(ttk.Frame):
    """
    Main dashboard with task selection cards.

    Displays a welcome message and three main task options:
    - Migrate Switch
    - Compare Switches
    - Settings
    """

    def __init__(
        self,
        parent,
        on_migrate: Optional[Callable[[], None]] = None,
        on_compare: Optional[Callable[[], None]] = None,
        on_settings: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Initialize the dashboard.

        Args:
            parent: Parent widget
            on_migrate: Callback when Migrate task is selected
            on_compare: Callback when Compare task is selected
            on_settings: Callback when Settings is selected
        """
        super().__init__(parent, **kwargs)
        self.on_migrate = on_migrate
        self.on_compare = on_compare
        self.on_settings = on_settings

        self._create_ui()

    def _create_ui(self):
        """Create the dashboard UI."""
        # Welcome header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=Spacing.XL, pady=(Spacing.XL, Spacing.LG))

        welcome_label = ttk.Label(
            header_frame,
            text="Welcome! What would you like to do?",
            style="Header.TLabel",
            font=Fonts.HEADER
        )
        welcome_label.pack(anchor=tk.W)

        subtitle_label = ttk.Label(
            header_frame,
            text="Select a task below to get started",
            style="Secondary.TLabel"
        )
        subtitle_label.pack(anchor=tk.W, pady=(Spacing.XS, 0))

        # Cards container
        cards_frame = ttk.Frame(self)
        cards_frame.pack(fill=tk.BOTH, expand=True, padx=Spacing.XL, pady=Spacing.MD)

        # Configure grid weights for responsive layout with minimum sizes
        cards_frame.columnconfigure(0, weight=1, minsize=280)
        cards_frame.columnconfigure(1, weight=1, minsize=280)
        cards_frame.rowconfigure(0, weight=1, minsize=200)
        cards_frame.rowconfigure(1, weight=1, minsize=200)

        # Migrate Switch card
        self.migrate_card = TaskCard(
            cards_frame,
            title="Migrate Switch",
            description="Convert your old Catalyst switch settings to Meraki format",
            icon="\U0001F504",  # Rotating arrows emoji
            on_click=self._on_migrate_click
        )
        self.migrate_card.grid(
            row=0, column=0,
            sticky="nsew",
            padx=(0, Spacing.MD),
            pady=(0, Spacing.MD)
        )

        # Compare Switches card
        self.compare_card = TaskCard(
            cards_frame,
            title="Compare Switches",
            description="Check if your migration was successful by comparing port status and connected devices",
            icon="\U0001F4CA",  # Bar chart emoji
            on_click=self._on_compare_click
        )
        self.compare_card.grid(
            row=0, column=1,
            sticky="nsew",
            padx=(Spacing.MD, 0),
            pady=(0, Spacing.MD)
        )

        # Settings card (spans one column, left side of second row)
        self.settings_card = TaskCard(
            cards_frame,
            title="Settings",
            description="Configure API keys, credentials, and application preferences",
            icon="\u2699",  # Gear symbol
            on_click=self._on_settings_click
        )
        self.settings_card.grid(
            row=1, column=0,
            sticky="nsew",
            padx=(0, Spacing.MD),
            pady=(Spacing.MD, 0)
        )

        # Info panel (right side of second row)
        info_frame = ttk.Frame(cards_frame, style="Card.TFrame")
        info_frame.grid(
            row=1, column=1,
            sticky="nsew",
            padx=(Spacing.MD, 0),
            pady=(Spacing.MD, 0)
        )

        # Info content
        info_container = tk.Frame(
            info_frame,
            bg=Colors.BG_CARD,
            highlightthickness=1,
            highlightbackground=Colors.BORDER
        )
        info_container.pack(fill=tk.BOTH, expand=True)

        info_inner = tk.Frame(info_container, bg=Colors.BG_CARD)
        info_inner.pack(fill=tk.BOTH, expand=True, padx=Spacing.LG, pady=Spacing.LG)

        info_title = tk.Label(
            info_inner,
            text="Quick Tips",
            font=Fonts.BOLD,
            fg=Colors.SECONDARY,
            bg=Colors.BG_CARD,
            anchor=tk.W
        )
        info_title.pack(fill=tk.X)

        tips = [
            "\u2022 Make sure you have Meraki API key configured in Settings",
            "\u2022 You can connect to the old switch or use a config file",
            "\u2022 Compare switches after migration to verify success"
        ]

        for tip in tips:
            tip_label = tk.Label(
                info_inner,
                text=tip,
                font=Fonts.SMALL,
                fg=Colors.TEXT_SECONDARY,
                bg=Colors.BG_CARD,
                anchor=tk.W,
                justify=tk.LEFT,
                wraplength=200
            )
            tip_label.pack(fill=tk.X, pady=(Spacing.SM, 0))

    def _on_migrate_click(self):
        """Handle Migrate card click."""
        if self.on_migrate:
            self.on_migrate()

    def _on_compare_click(self):
        """Handle Compare card click."""
        if self.on_compare:
            self.on_compare()

    def _on_settings_click(self):
        """Handle Settings card click."""
        if self.on_settings:
            self.on_settings()
