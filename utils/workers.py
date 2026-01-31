"""
Threading utilities for running tasks in the background.
"""

import threading
import sys
import traceback
from tkinter import messagebox
from .console_redirect import ConsoleRedirector

class BackgroundTask:
    """
    Handles running tasks in background threads to keep the UI responsive.
    """
    
    @staticmethod
    def run(task_function, console_widget=None, success_callback=None, error_callback=None):
        """
        Run a task in a background thread.
        
        Args:
            task_function: The function to run in the background
            console_widget: Optional tkinter widget to redirect stdout to
            success_callback: Optional function to call on successful completion
            error_callback: Optional function to call on error
        """
        def run_task():
            original_stdout = sys.stdout
            try:
                # Redirect stdout if a console widget is provided
                if console_widget:
                    redirector = ConsoleRedirector(console_widget)
                    sys.stdout = redirector
                
                # Run the task
                result = task_function()
                
                # Call the success callback if provided
                if success_callback:
                    success_callback(result)
                    
            except Exception as e:
                # Print the error to the console
                if console_widget:
                    console_widget.insert("end", f"\nError: {str(e)}\n")
                    traceback.print_exc(file=sys.stdout)
                
                # Call the error callback if provided
                if error_callback:
                    error_callback(e)
                else:
                    messagebox.showerror("Error", f"An error occurred: {str(e)}")
            finally:
                # Restore stdout
                sys.stdout = original_stdout
        
        # Create and start the thread
        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()
        return thread