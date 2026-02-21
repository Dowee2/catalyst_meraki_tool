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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """Main application entry point"""
    if sys.platform.startswith('win'):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root = tk.Tk()
    root.title("Catalyst to Meraki Migration Tool")
    root.geometry("1024x768")
    root.minsize(900, 650)
    root.configure(bg=Colors.BG_MAIN)

    app = AppController(root)

    root.mainloop()

if __name__ == "__main__":
    main()
