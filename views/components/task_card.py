"""
Large clickable task card for the dashboard.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from config.theme import Colors, Fonts, Spacing


class TaskCard(ttk.Frame):
    """
    A large clickable card that represents a task on the dashboard.

    Features:
    - Icon, title, and description
    - Hover effects
    - Click handler
    """

    def __init__(
        self,
        parent,
        title: str,
        description: str,
        icon: str = "",
        on_click: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Initialize a task card.

        Args:
            parent: Parent widget
            title: Card title (main text)
            description: Card description (secondary text)
            icon: Optional icon character (emoji or unicode)
            on_click: Callback when card is clicked
        """
        super().__init__(parent, **kwargs)
        self.title_text = title
        self.description_text = description
        self.icon_text = icon
        self.on_click = on_click
        self._is_hovered = False

        self._create_ui()
        self._bind_events()

    def _create_ui(self):
        """Create the card UI."""
        # Main card container using a Canvas for background control
        self.card = tk.Canvas(
            self,
            bg=Colors.BG_CARD,
            highlightthickness=1,
            highlightbackground=Colors.BORDER,
            cursor="hand2"
        )
        self.card.pack(fill=tk.BOTH, expand=True)

        # Configure minimum size
        self.card.configure(width=200, height=150)

        # Create internal frame for content
        self.content_frame = ttk.Frame(self.card, style="Card.TFrame")
        self.card_window = self.card.create_window(
            0, 0,
            window=self.content_frame,
            anchor=tk.NW,
            tags="content"
        )

        # Icon (if provided)
        if self.icon_text:
            self.icon_label = ttk.Label(
                self.content_frame,
                text=self.icon_text,
                style="Card.TLabel",
                font=('Segoe UI', 32)
            )
            self.icon_label.pack(pady=(Spacing.LG, Spacing.SM))

        # Title
        self.title_label = ttk.Label(
            self.content_frame,
            text=self.title_text,
            style="Card.TLabel",
            font=Fonts.LARGE_BOLD
        )
        self.title_label.pack(pady=(Spacing.SM, Spacing.XS))

        # Description
        self.desc_label = ttk.Label(
            self.content_frame,
            text=self.description_text,
            style="Card.TLabel",
            font=Fonts.SMALL,
            foreground=Colors.TEXT_SECONDARY,
            wraplength=180,
            justify=tk.CENTER
        )
        self.desc_label.pack(pady=(0, Spacing.LG))

        # Handle resize to position content
        self.card.bind('<Configure>', self._on_resize)

    def _on_resize(self, event):
        """Handle card resize to center content."""
        # Update window position to center
        self.card.coords(
            self.card_window,
            event.width // 2,
            event.height // 2
        )
        # Reconfigure anchor to center
        self.card.itemconfigure(self.card_window, anchor=tk.CENTER)

    def _bind_events(self):
        """Bind mouse events for hover and click."""
        # Bind to card and all children
        widgets = [self.card, self.content_frame]
        if hasattr(self, 'icon_label'):
            widgets.append(self.icon_label)
        widgets.extend([self.title_label, self.desc_label])

        for widget in widgets:
            widget.bind('<Enter>', self._on_enter)
            widget.bind('<Leave>', self._on_leave)
            widget.bind('<Button-1>', self._on_click)

    def _on_enter(self, event):
        """Handle mouse enter."""
        if not self._is_hovered:
            self._is_hovered = True
            self.card.configure(
                bg=Colors.PRIMARY,
                highlightbackground=Colors.PRIMARY
            )
            # Update label colors for contrast
            self.title_label.configure(foreground=Colors.TEXT_BUTTON)
            self.desc_label.configure(foreground=Colors.TEXT_BUTTON)
            if hasattr(self, 'icon_label'):
                self.icon_label.configure(foreground=Colors.TEXT_BUTTON)

    def _on_leave(self, event):
        """Handle mouse leave."""
        # Check if we're still within the card bounds
        x, y = self.card.winfo_pointerxy()
        card_x = self.card.winfo_rootx()
        card_y = self.card.winfo_rooty()
        card_w = self.card.winfo_width()
        card_h = self.card.winfo_height()

        if not (card_x <= x <= card_x + card_w and
                card_y <= y <= card_y + card_h):
            self._is_hovered = False
            self.card.configure(
                bg=Colors.BG_CARD,
                highlightbackground=Colors.BORDER
            )
            # Restore label colors
            self.title_label.configure(foreground=Colors.TEXT_PRIMARY)
            self.desc_label.configure(foreground=Colors.TEXT_SECONDARY)
            if hasattr(self, 'icon_label'):
                self.icon_label.configure(foreground=Colors.TEXT_PRIMARY)

    def _on_click(self, event):
        """Handle mouse click."""
        if self.on_click:
            self.on_click()

    def set_enabled(self, enabled: bool):
        """Enable or disable the card."""
        if enabled:
            self.card.configure(cursor="hand2")
            self._bind_events()
        else:
            self.card.configure(cursor="arrow")
            # Unbind events
            widgets = [self.card, self.content_frame, self.title_label, self.desc_label]
            if hasattr(self, 'icon_label'):
                widgets.append(self.icon_label)
            for widget in widgets:
                widget.unbind('<Enter>')
                widget.unbind('<Leave>')
                widget.unbind('<Button-1>')
