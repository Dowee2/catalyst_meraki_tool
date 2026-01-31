"""
Dialog for managing Meraki serial numbers.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import re

from config.theme import Colors, Fonts, Spacing

class SerialListManager(tk.Toplevel):
    """
    Dialog for managing a list of Meraki serial numbers.
    """
    
    def __init__(self, parent, serial_list=None, title="Manage Meraki Serial Numbers"):
        """
        Initialize the serial list manager.
        
        Args:
            parent: The parent window
            serial_list (list, optional): List of serial numbers
            title (str): Dialog title
        """
        super().__init__(parent)
        self.title(title)
        self.geometry("500x400")
        self.configure(bg=Colors.BG_MAIN)
        self.transient(parent)
        self.grab_set()

        self.result = None
        self.parent = parent

        # Initialize with existing list if provided
        if serial_list:
            self.serial_list = serial_list.copy()
        else:
            self.serial_list = []

        # Main frame
        main_frame = ttk.Frame(self, padding=Spacing.MD)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Serial input frame
        input_frame = ttk.LabelFrame(main_frame, text="Add Serial Number")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Serial Number:").grid(
            row=0, column=0, padx=Spacing.SM, pady=Spacing.SM, sticky=tk.W)
        self.serial_entry = ttk.Entry(input_frame, width=30)
        self.serial_entry.grid(row=0, column=1, padx=Spacing.SM, pady=Spacing.SM, sticky=tk.W)

        ttk.Button(input_frame, text="Add", command=self.add_serial,
                   style="Primary.TButton").grid(row=0, column=2, padx=Spacing.SM, pady=Spacing.SM)
        
        # List display frame
        list_frame = ttk.LabelFrame(main_frame, text="Serial Numbers")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a listbox with scrollbar
        self.serial_listbox = tk.Listbox(
            list_frame, selectmode=tk.SINGLE, height=10,
            font=Fonts.NORMAL, bg=Colors.BG_CARD, fg=Colors.TEXT_PRIMARY,
            selectbackground=Colors.PRIMARY, selectforeground=Colors.TEXT_BUTTON)
        self.serial_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=Spacing.SM, pady=Spacing.SM)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.serial_listbox.yview)
        self.serial_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=5)
        
        # Populate list
        self.refresh_list()
        
        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, padx=Spacing.SM, pady=Spacing.SM)

        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_serial,
                   style="Secondary.TButton").pack(side=tk.LEFT, padx=Spacing.SM, pady=Spacing.SM)
        ttk.Button(btn_frame, text="Move Up", command=self.move_up,
                   style="Secondary.TButton").pack(side=tk.LEFT, padx=Spacing.SM, pady=Spacing.SM)
        ttk.Button(btn_frame, text="Move Down", command=self.move_down,
                   style="Secondary.TButton").pack(side=tk.LEFT, padx=Spacing.SM, pady=Spacing.SM)
        ttk.Button(btn_frame, text="Import...", command=self.import_serials,
                   style="Secondary.TButton").pack(side=tk.LEFT, padx=Spacing.SM, pady=Spacing.SM)
        ttk.Button(btn_frame, text="Save", command=self.save,
                   style="Primary.TButton").pack(side=tk.RIGHT, padx=Spacing.SM, pady=Spacing.SM)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel,
                   style="Secondary.TButton").pack(side=tk.RIGHT, padx=Spacing.SM, pady=Spacing.SM)

        # Help text
        help_text = "Note: The order of serial numbers is important for stacked switches."
        ttk.Label(main_frame, text=help_text, font=Fonts.ITALIC,
                  style="Secondary.TLabel").pack(anchor=tk.W, padx=Spacing.SM, pady=(Spacing.MD, 0))
        
        # Bind double-click to edit
        self.serial_listbox.bind('<Double-1>', self.edit_serial)
        
        # Center the dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
        # Set focus to entry
        self.serial_entry.focus_set()
        
    def refresh_list(self):
        """Refresh the listbox with current serial numbers."""
        self.serial_listbox.delete(0, tk.END)
        for i, serial in enumerate(self.serial_list):
            self.serial_listbox.insert(tk.END, f"{i+1}: {serial}")
            
    def add_serial(self):
        """Add a new serial number to the list."""
        serial = self.serial_entry.get().strip()
        if serial:
            # Validate serial format (simple validation)
            if not self.validate_serial(serial):
                messagebox.showwarning("Warning", "Invalid serial number format")
                return
                
            self.serial_list.append(serial)
            self.refresh_list()
            self.serial_entry.delete(0, tk.END)
            self.serial_entry.focus_set()
        else:
            messagebox.showwarning("Warning", "Serial number cannot be empty")
            
    def validate_serial(self, serial):
        """
        Validate the serial number format.
        
        Args:
            serial (str): The serial number to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Simple validation - can be enhanced as needed
        pattern = r"^[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}$"
        return re.match(pattern, serial)
            
    def edit_serial(self, event=None):
        """Edit the selected serial number."""
        selected = self.serial_listbox.curselection()
        if selected:
            index = selected[0]
            current = self.serial_list[index]
            
            # Ask for new value
            new_serial = simpledialog.askstring("Edit Serial", 
                                                "Enter new serial number:", 
                                                initialvalue=current,
                                                parent=self)
            
            if new_serial and new_serial.strip():
                # Validate serial format
                if not self.validate_serial(new_serial.strip()):
                    messagebox.showwarning("Warning", "Invalid serial number format")
                    return
                    
                self.serial_list[index] = new_serial.strip()
                self.refresh_list()
                
    def remove_serial(self):
        """Remove the selected serial number."""
        selected = self.serial_listbox.curselection()
        if selected:
            index = selected[0]
            del self.serial_list[index]
            self.refresh_list()
            
    def move_up(self):
        """Move the selected serial up in the list."""
        selected = self.serial_listbox.curselection()
        if selected:
            index = selected[0]
            if index > 0:
                self.serial_list[index], self.serial_list[index-1] = self.serial_list[index-1], self.serial_list[index]
                self.refresh_list()
                self.serial_listbox.selection_set(index-1)
                
    def move_down(self):
        """Move the selected serial down in the list."""
        selected = self.serial_listbox.curselection()
        if selected:
            index = selected[0]
            if index < len(self.serial_list) - 1:
                self.serial_list[index], self.serial_list[index+1] = self.serial_list[index+1], self.serial_list[index]
                self.refresh_list()
                self.serial_listbox.selection_set(index+1)
    
    def import_serials(self):
        """Import serials from a text input."""
        dialog = ImportSerialsDialog(self)
        self.wait_window(dialog)
        
        if dialog.result:
            # Add the imported serials to the list
            for serial in dialog.result:
                if serial not in self.serial_list:
                    self.serial_list.append(serial)
            self.refresh_list()
                
    def save(self):
        """Save the list and close the dialog."""
        self.result = self.serial_list.copy()
        self.destroy()
        
    def cancel(self):
        """Cancel and close without saving."""
        self.result = None
        self.destroy()


class ImportSerialsDialog(tk.Toplevel):
    """
    Dialog for importing multiple serial numbers at once.
    """
    
    def __init__(self, parent):
        """
        Initialize the import dialog.
        
        Args:
            parent: The parent window
        """
        super().__init__(parent)
        self.title("Import Serial Numbers")
        self.geometry("500x300")
        self.configure(bg=Colors.BG_MAIN)
        self.transient(parent)
        self.grab_set()

        self.result = None
        self.parent = parent

        # Main frame
        main_frame = ttk.Frame(self, padding=Spacing.MD)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Instructions
        instructions = """Enter or paste serial numbers below, one per line.
Empty lines and invalid formats will be ignored."""
        ttk.Label(main_frame, text=instructions,
                  style="Secondary.TLabel").pack(anchor=tk.W, padx=Spacing.SM, pady=Spacing.SM)

        # Text input
        self.serial_text = tk.Text(
            main_frame, height=10, width=50,
            font=Fonts.NORMAL, bg=Colors.BG_CARD, fg=Colors.TEXT_PRIMARY,
            insertbackground=Colors.PRIMARY)
        self.serial_text.pack(fill=tk.BOTH, expand=True, padx=Spacing.SM, pady=Spacing.SM)

        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, padx=Spacing.SM, pady=Spacing.MD)

        ttk.Button(btn_frame, text="Import", command=self.import_serials,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=Spacing.SM)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel,
                   style="Secondary.TButton").pack(side=tk.LEFT, padx=Spacing.SM)
        
        # Center the dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
        # Set focus to text input
        self.serial_text.focus_set()
        
    def import_serials(self):
        """Process and import the serial numbers."""
        text = self.serial_text.get("1.0", tk.END)
        lines = text.strip().split('\n')
        
        # Filter and validate serials
        valid_serials = []
        for line in lines:
            serial = line.strip()
            if serial and len(serial) >= 4 and serial.isalnum():
                valid_serials.append(serial)
        
        if valid_serials:
            self.result = valid_serials
            self.destroy()
        else:
            messagebox.showwarning("Warning", "No valid serial numbers found")
            
    def cancel(self):
        """Cancel and close."""
        self.result = None
        self.destroy()