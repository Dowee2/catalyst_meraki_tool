"""
Large clickable task card for the dashboard.
"""

import tkinter as tk
from typing import Callable, Optional

from config.theme import Colors, Fonts, Spacing


class TaskCard(tk.Frame):
    """
    A large clickable card that represents a task on the dashboard.

    Features:
    - Icon, title, and description
    - Hover effects with proper color transitions
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
        super().__init__(parent, bg=Colors.BG_MAIN, **kwargs)
        self.title_text = title
        self.description_text = description
        self.icon_text = icon
        self.on_click = on_click
        self._is_hovered = False

        # Colors for normal and hover states
        self._bg_normal = Colors.BG_CARD
        self._bg_hover = Colors.PRIMARY
        self._fg_normal = Colors.TEXT_PRIMARY
        self._fg_hover = Colors.TEXT_BUTTON
        self._fg_secondary_normal = Colors.TEXT_SECONDARY
        self._fg_secondary_hover = Colors.TEXT_BUTTON

        self._create_ui()
        self._bind_events()

    def _create_ui(self):
        """Create the card UI."""
        # Card container with border effect
        self.card = tk.Frame(
            self,
            bg=self._bg_normal,
            highlightthickness=1,
            highlightbackground=Colors.BORDER,
            cursor="hand2"
        )
        self.card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Inner content frame for padding
        self.content = tk.Frame(self.card, bg=self._bg_normal)
        self.content.pack(fill=tk.BOTH, expand=True, padx=Spacing.LG, pady=Spacing.LG)

        # Center content vertically
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_rowconfigure(4, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Spacer at top
        tk.Frame(self.content, bg=self._bg_normal, height=10).grid(row=0, column=0, sticky="nsew")

        # Icon (if provided)
        if self.icon_text:
            self.icon_label = tk.Label(
                self.content,
                text=self.icon_text,
                bg=self._bg_normal,
                fg=self._fg_normal,
                font=('Segoe UI', 36)
            )
            self.icon_label.grid(row=1, column=0, pady=(0, Spacing.SM))

        # Title
        self.title_label = tk.Label(
            self.content,
            text=self.title_text,
            bg=self._bg_normal,
            fg=self._fg_normal,
            font=Fonts.LARGE_BOLD
        )
        self.title_label.grid(row=2, column=0, pady=(Spacing.SM, Spacing.XS))

        # Description
        self.desc_label = tk.Label(
            self.content,
            text=self.description_text,
            bg=self._bg_normal,
            fg=self._fg_secondary_normal,
            font=Fonts.SMALL,
            wraplength=200,
            justify=tk.CENTER
        )
        self.desc_label.grid(row=3, column=0, pady=(0, Spacing.SM))

        # Spacer at bottom
        tk.Frame(self.content, bg=self._bg_normal, height=10).grid(row=4, column=0, sticky="nsew")

        # Store all widgets that need color updates
        self._widgets = [self.card, self.content]
        if hasattr(self, 'icon_label'):
            self._widgets.append(self.icon_label)
        self._widgets.extend([self.title_label, self.desc_label])

        # Add spacer frames
        for child in self.content.winfo_children():
            if isinstance(child, tk.Frame):
                self._widgets.append(child)

    def _bind_events(self):
        """Bind mouse events for hover and click."""
        for widget in self._widgets:
            widget.bind('<Enter>', self._on_enter)
            widget.bind('<Leave>', self._on_leave)
            widget.bind('<Button-1>', self._on_click)

    def _set_colors(self, bg, fg, fg_secondary):
        """Update all widget colors."""
        for widget in self._widgets:
            widget.configure(bg=bg)

        self.title_label.configure(fg=fg)
        if hasattr(self, 'icon_label'):
            self.icon_label.configure(fg=fg)
        self.desc_label.configure(fg=fg_secondary)

    def _on_enter(self, event):
        """Handle mouse enter."""
        if not self._is_hovered:
            self._is_hovered = True
            self._set_colors(self._bg_hover, self._fg_hover, self._fg_secondary_hover)
            self.card.configure(highlightbackground=self._bg_hover)

    def _on_leave(self, event):
        """Handle mouse leave."""
        # Check if we're still within the card bounds
        x, y = self.winfo_pointerxy()
        card_x = self.card.winfo_rootx()
        card_y = self.card.winfo_rooty()
        card_w = self.card.winfo_width()
        card_h = self.card.winfo_height()

        if not (card_x <= x <= card_x + card_w and
                card_y <= y <= card_y + card_h):
            self._is_hovered = False
            self._set_colors(self._bg_normal, self._fg_normal, self._fg_secondary_normal)
            self.card.configure(highlightbackground=Colors.BORDER)

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
            for widget in self._widgets:
                widget.unbind('<Enter>')
                widget.unbind('<Leave>')
                widget.unbind('<Button-1>')
