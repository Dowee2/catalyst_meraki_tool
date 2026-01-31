"""
Visual progress indicator for wizard steps.
"""

import tkinter as tk
from tkinter import ttk

from config.theme import Colors, Fonts, Spacing


class WizardProgressBar(ttk.Frame):
    """
    A visual progress bar showing wizard steps.

    Displays circles for each step connected by lines,
    with the current step highlighted.
    """

    def __init__(self, parent, steps, current_step=0):
        """
        Initialize the progress bar.

        Args:
            parent: Parent widget
            steps: List of step names/titles
            current_step: Index of current step (0-based)
        """
        super().__init__(parent)
        self.steps = steps
        self.current_step = current_step
        self.step_widgets = []

        self._create_ui()

    def _create_ui(self):
        """Create the progress bar UI."""
        # Container for the progress bar
        self.canvas = tk.Canvas(
            self, height=80, bg=Colors.BG_CARD,
            highlightthickness=0)
        self.canvas.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.SM)

        # Bind resize event
        self.canvas.bind('<Configure>', self._draw_progress)

    def _draw_progress(self, event=None):
        """Draw the progress bar with circles and lines."""
        self.canvas.delete('all')

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 100 or len(self.steps) == 0:
            return

        # Calculate positions
        num_steps = len(self.steps)
        padding = 60
        available_width = width - (padding * 2)
        step_spacing = available_width / (num_steps - 1) if num_steps > 1 else 0
        circle_radius = 16
        y_center = 35

        # Draw connecting lines first (behind circles)
        for i in range(num_steps - 1):
            x1 = padding + (i * step_spacing) + circle_radius
            x2 = padding + ((i + 1) * step_spacing) - circle_radius

            # Line color based on completion
            if i < self.current_step:
                line_color = Colors.PRIMARY
            else:
                line_color = Colors.BORDER

            self.canvas.create_line(
                x1, y_center, x2, y_center,
                fill=line_color, width=3)

        # Draw circles and labels
        for i, step_name in enumerate(self.steps):
            x = padding + (i * step_spacing)

            # Determine circle style
            if i < self.current_step:
                # Completed step
                fill_color = Colors.PRIMARY
                outline_color = Colors.PRIMARY
                text_color = Colors.TEXT_BUTTON
                label_color = Colors.TEXT_SECONDARY
                symbol = "\u2713"  # Checkmark
            elif i == self.current_step:
                # Current step
                fill_color = Colors.PRIMARY
                outline_color = Colors.PRIMARY
                text_color = Colors.TEXT_BUTTON
                label_color = Colors.PRIMARY
                symbol = str(i + 1)
            else:
                # Future step
                fill_color = Colors.BG_CARD
                outline_color = Colors.BORDER
                text_color = Colors.TEXT_SECONDARY
                label_color = Colors.TEXT_SECONDARY
                symbol = str(i + 1)

            # Draw circle
            self.canvas.create_oval(
                x - circle_radius, y_center - circle_radius,
                x + circle_radius, y_center + circle_radius,
                fill=fill_color, outline=outline_color, width=2)

            # Draw number/checkmark
            self.canvas.create_text(
                x, y_center,
                text=symbol, fill=text_color,
                font=('Segoe UI', 10, 'bold'))

            # Draw step label below
            self.canvas.create_text(
                x, y_center + 30,
                text=step_name, fill=label_color,
                font=('Segoe UI', 9),
                width=step_spacing - 10 if step_spacing > 0 else 100)

    def set_step(self, step_index):
        """
        Update the current step.

        Args:
            step_index: New current step index (0-based)
        """
        self.current_step = step_index
        self._draw_progress()

    def next_step(self):
        """Move to the next step if possible."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._draw_progress()
            return True
        return False

    def prev_step(self):
        """Move to the previous step if possible."""
        if self.current_step > 0:
            self.current_step -= 1
            self._draw_progress()
            return True
        return False
