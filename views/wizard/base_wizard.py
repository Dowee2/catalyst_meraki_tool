"""
Base wizard container with navigation and progress bar.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from config.theme import Colors, Fonts, Spacing
from views.wizard.progress_bar import WizardProgressBar


class BaseWizard(ttk.Frame):
    """
    A wizard container that manages steps with navigation.

    Features:
    - Progress bar showing current step
    - Step content area
    - Back, Next, Cancel navigation buttons
    - Step validation before navigation
    - Callbacks for completion and cancellation
    """

    def __init__(
        self,
        parent,
        steps: list[dict],
        on_complete: Optional[Callable[[dict], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Initialize the wizard.

        Args:
            parent: Parent widget
            steps: List of step definitions, each with:
                - 'name': Display name for progress bar
                - 'title': Step header title
                - 'description': Optional description text
                - 'create_content': Callable(content_frame) to create step UI
                - 'validate': Optional Callable() -> (bool, str) for validation
                - 'on_enter': Optional Callable() when entering step
                - 'on_leave': Optional Callable() when leaving step
            on_complete: Callback when wizard finishes (receives collected data)
            on_cancel: Callback when wizard is cancelled
        """
        super().__init__(parent, **kwargs)
        self.steps = steps
        self.current_step = 0
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self.data = {}  # Collected data from all steps
        self.step_frames = []

        self._create_ui()
        self._show_step(0)

    def _create_ui(self):
        """Create the wizard UI layout."""
        # Main container with card background
        self.configure(style="Card.TFrame")

        # Progress bar at top
        step_names = [step.get('name', f'Step {i+1}')
                      for i, step in enumerate(self.steps)]
        self.progress_bar = WizardProgressBar(self, step_names)
        self.progress_bar.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD)

        # Separator below progress bar
        separator = ttk.Separator(self, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, padx=Spacing.MD)

        # Step content container (will hold one step at a time)
        self.content_container = ttk.Frame(self, style="Card.TFrame")
        self.content_container.pack(
            fill=tk.BOTH, expand=True, padx=Spacing.MD, pady=Spacing.SM)

        # Create all step frames (hidden by default)
        for i, step in enumerate(self.steps):
            step_frame = self._create_step_frame(step)
            self.step_frames.append(step_frame)

        # Separator above buttons
        separator_bottom = ttk.Separator(self, orient=tk.HORIZONTAL)
        separator_bottom.pack(fill=tk.X, padx=Spacing.MD, pady=(Spacing.SM, 0))

        # Navigation buttons at bottom
        self._create_navigation_buttons()

    def _create_step_frame(self, step: dict) -> ttk.Frame:
        """Create a frame for a single step."""
        frame = ttk.Frame(self.content_container, style="Card.TFrame")

        # Header section
        header_frame = ttk.Frame(frame, style="Card.TFrame")
        header_frame.pack(fill=tk.X, padx=Spacing.LG, pady=(Spacing.MD, Spacing.SM))

        # Step title
        title_label = ttk.Label(
            header_frame,
            text=step.get('title', ''),
            style="Card.TLabel",
            font=Fonts.HEADER)
        title_label.pack(anchor=tk.W)

        # Step description
        description = step.get('description', '')
        if description:
            desc_label = ttk.Label(
                header_frame,
                text=description,
                style="Card.TLabel",
                font=Fonts.SMALL,
                foreground=Colors.TEXT_SECONDARY,
                wraplength=600)
            desc_label.pack(anchor=tk.W, pady=(Spacing.XS, 0))

        # Content area for step-specific widgets
        content_frame = ttk.Frame(frame, style="Card.TFrame")
        content_frame.pack(
            fill=tk.BOTH, expand=True,
            padx=Spacing.LG, pady=Spacing.MD)

        # Let the step create its content
        create_content = step.get('create_content')
        if create_content:
            create_content(content_frame)

        return frame

    def _create_navigation_buttons(self):
        """Create the navigation button bar."""
        button_frame = ttk.Frame(self, style="Card.TFrame")
        button_frame.pack(fill=tk.X, padx=Spacing.LG, pady=Spacing.MD)

        # Left side - Cancel button
        self.cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            style="Secondary.TButton",
            command=self._on_cancel)
        self.cancel_btn.pack(side=tk.LEFT)

        # Right side - Back and Next buttons
        self.next_btn = ttk.Button(
            button_frame,
            text="Next",
            style="Primary.TButton",
            command=self._on_next)
        self.next_btn.pack(side=tk.RIGHT)

        self.back_btn = ttk.Button(
            button_frame,
            text="Back",
            style="Secondary.TButton",
            command=self._on_back)
        self.back_btn.pack(side=tk.RIGHT, padx=(0, Spacing.SM))

        # Error message label (hidden by default)
        self.error_label = ttk.Label(
            button_frame,
            text="",
            foreground=Colors.ERROR,
            style="Card.TLabel",
            font=Fonts.SMALL)
        self.error_label.pack(side=tk.LEFT, padx=Spacing.MD)

    def _show_step(self, step_index: int):
        """Show a specific step and hide others."""
        # Hide all steps
        for frame in self.step_frames:
            frame.pack_forget()

        # Show the requested step
        self.step_frames[step_index].pack(fill=tk.BOTH, expand=True)

        # Update progress bar
        self.progress_bar.set_step(step_index)

        # Update button states
        self._update_buttons()

        # Clear any error message
        self.error_label.config(text="")

        # Call on_enter callback if defined
        on_enter = self.steps[step_index].get('on_enter')
        if on_enter:
            on_enter()

    def _update_buttons(self):
        """Update navigation button states and text."""
        # Back button - disabled on first step
        if self.current_step == 0:
            self.back_btn.state(['disabled'])
        else:
            self.back_btn.state(['!disabled'])

        # Next button - change text on last step
        if self.current_step == len(self.steps) - 1:
            self.next_btn.config(text="Finish")
        else:
            self.next_btn.config(text="Next")

    def _validate_current_step(self) -> tuple[bool, str]:
        """
        Validate the current step.

        Returns:
            Tuple of (is_valid, error_message)
        """
        validate_func = self.steps[self.current_step].get('validate')
        if validate_func:
            return validate_func()
        return True, ""

    def _on_next(self):
        """Handle Next button click."""
        # Validate current step
        is_valid, error_msg = self._validate_current_step()
        if not is_valid:
            self.error_label.config(text=error_msg)
            return

        # Call on_leave callback
        on_leave = self.steps[self.current_step].get('on_leave')
        if on_leave:
            on_leave()

        # Move to next step or complete
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._show_step(self.current_step)
        else:
            self._complete()

    def _on_back(self):
        """Handle Back button click."""
        if self.current_step > 0:
            # Call on_leave callback
            on_leave = self.steps[self.current_step].get('on_leave')
            if on_leave:
                on_leave()

            self.current_step -= 1
            self._show_step(self.current_step)

    def _on_cancel(self):
        """Handle Cancel button click."""
        if self.on_cancel:
            self.on_cancel()

    def _complete(self):
        """Complete the wizard."""
        if self.on_complete:
            self.on_complete(self.data)

    def set_data(self, key: str, value):
        """
        Store data collected from a step.

        Args:
            key: Data key
            value: Data value
        """
        self.data[key] = value

    def get_data(self, key: str, default=None):
        """
        Retrieve stored data.

        Args:
            key: Data key
            default: Default value if key not found

        Returns:
            The stored value or default
        """
        return self.data.get(key, default)

    def go_to_step(self, step_index: int):
        """
        Jump to a specific step (for programmatic navigation).

        Args:
            step_index: Index of step to show (0-based)
        """
        if 0 <= step_index < len(self.steps):
            self.current_step = step_index
            self._show_step(step_index)

    def enable_next(self):
        """Enable the Next button."""
        self.next_btn.state(['!disabled'])

    def disable_next(self):
        """Disable the Next button."""
        self.next_btn.state(['disabled'])

    def show_error(self, message: str):
        """Display an error message."""
        self.error_label.config(text=message)

    def clear_error(self):
        """Clear the error message."""
        self.error_label.config(text="")
