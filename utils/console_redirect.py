"""
Console redirection utility for redirecting stdout to a tkinter Text widget.
"""

import tkinter as tk

class ConsoleRedirector:
    """
    Class to redirect stdout to a tkinter Text widget.

    This is useful for displaying console output in the GUI.
    """
    def __init__(self, text_widget):
        """
        Initialize the redirector.

        Args:
            text_widget: A tkinter Text or ScrolledText widget
        """
        self.text_widget = text_widget
        self.buffer = ""

    def write(self, string):
        """
        Write a string to the text widget.

        Args:
            string: The string to write
        """
        self.buffer += string
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)

    def flush(self):
        """
        Flush the buffer. Required for stdout redirection.
        """
        self.text_widget.update_idletasks()
