#!/usr/bin/env python3
"""
Catalyst to Meraki Migration Tools
This tool helps network administrators migrate configurations from Cisco Catalyst 
switches to Cisco Meraki switches.
"""


from controllers.app_controller import AppController
from config.theme import Colors
import tkinter as tk
import ctypes
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """Main application entry point"""
    # Fix for Windows to properly show the console output
    if sys.platform.startswith('win'):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    
    # Create the main application window
    root = tk.Tk()
    root.title("Catalyst to Meraki Migration Tool")
    root.geometry("1024x768")
    root.minsize(900, 650)
    root.configure(bg=Colors.BG_MAIN)
    
    # Create the application controller
    app = AppController(root)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()