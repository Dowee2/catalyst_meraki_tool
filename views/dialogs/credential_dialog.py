"""
Dialog for managing switch credentials.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import getpass

from config.theme import Colors, Fonts, Spacing

class CredentialDialog(tk.Toplevel):
    """
    Dialog for entering a single set of switch credentials.
    """
    
    def __init__(self, parent, title="Enter Switch Credentials", initial_values=None):
        """
        Initialize the credential dialog.
        
        Args:
            parent: The parent window
            title (str): The dialog title
            initial_values (dict, optional): Initial values for username, password, and description
        """
        super().__init__(parent)
        self.title(title)
        self.geometry("400x200")
        self.configure(bg=Colors.BG_MAIN)
        self.transient(parent)
        self.grab_set()

        self.result = None
        self.parent = parent

        # Main frame
        main_frame = ttk.Frame(self, padding=Spacing.MD)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Username
        ttk.Label(main_frame, text="Username:").grid(row=0, column=0, padx=5, pady=10, sticky=tk.W)
        self.username = ttk.Entry(main_frame, width=30)
        self.username.grid(row=0, column=1, padx=5, pady=10, sticky=tk.W)
        
        # Default to current user or initial value
        if initial_values and 'username' in initial_values:
            self.username.insert(0, initial_values['username'])
        else:
            self.username.insert(0, getpass.getuser())
        
        # Password
        ttk.Label(main_frame, text="Password:").grid(row=1, column=0, padx=5, pady=10, sticky=tk.W)
        self.password = ttk.Entry(main_frame, width=30, show="*")
        self.password.grid(row=1, column=1, padx=5, pady=10, sticky=tk.W)
        
        # Add initial password if provided
        if initial_values and 'password' in initial_values:
            self.password.insert(0, initial_values['password'])
        
        # Optional description field
        ttk.Label(main_frame, text="Description:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.description = ttk.Entry(main_frame, width=30)
        self.description.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Add initial description if provided
        if initial_values and 'description' in initial_values:
            self.description.insert(0, initial_values['description'])
        
        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, padx=Spacing.SM, pady=Spacing.MD)

        ttk.Button(btn_frame, text="OK", command=self.save,
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
        
        # Set focus to username
        self.username.focus_set()
        
    def save(self):
        """Save the credentials and close the dialog."""
        username = self.username.get().strip()
        password = self.password.get()
        description = self.description.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Warning", "Username and password are required")
            return
            
        self.result = {
            'username': username,
            'password': password,
            'description': description if description else f"{username} credential"
        }
        self.destroy()
        
    def cancel(self):
        """Cancel and close the dialog."""
        self.result = None
        self.destroy()


class CredentialListManager(tk.Toplevel):
    """
    Dialog for managing multiple sets of credentials.
    """
    
    def __init__(self, parent, credentials_list=None):
        """
        Initialize the credential list manager.
        
        Args:
            parent: The parent window
            credentials_list (list, optional): List of credential dictionaries
        """
        super().__init__(parent)
        self.title("Manage Switch Credentials")
        self.geometry("600x400")
        self.configure(bg=Colors.BG_MAIN)
        self.transient(parent)
        self.grab_set()

        self.result = None
        self.parent = parent

        # Initialize with existing list if provided
        if credentials_list:
            self.credentials_list = credentials_list.copy()
        else:
            self.credentials_list = []

        # Main frame
        main_frame = ttk.Frame(self, padding=Spacing.MD)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Credential list display frame
        list_frame = ttk.LabelFrame(main_frame, text="Saved Credentials")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create Treeview for credentials
        columns = ("description", "username")
        self.credentials_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.credentials_tree.heading("description", text="Description")
        self.credentials_tree.heading("username", text="Username")
        
        self.credentials_tree.column("description", width=300)
        self.credentials_tree.column("username", width=200)
        
        self.credentials_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.credentials_tree.yview)
        self.credentials_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, padx=Spacing.SM, pady=Spacing.SM)

        ttk.Button(btn_frame, text="Add Credential", command=self.add_credential,
                   style="Secondary.TButton").pack(side=tk.LEFT, padx=Spacing.SM, pady=Spacing.SM)
        ttk.Button(btn_frame, text="Edit Selected", command=self.edit_credential,
                   style="Secondary.TButton").pack(side=tk.LEFT, padx=Spacing.SM, pady=Spacing.SM)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_credential,
                   style="Secondary.TButton").pack(side=tk.LEFT, padx=Spacing.SM, pady=Spacing.SM)
        ttk.Button(btn_frame, text="Save", command=self.save,
                   style="Primary.TButton").pack(side=tk.RIGHT, padx=Spacing.SM, pady=Spacing.SM)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel,
                   style="Secondary.TButton").pack(side=tk.RIGHT, padx=Spacing.SM, pady=Spacing.SM)
        
        # Populate list
        self.refresh_list()
        
        # Bind double-click to edit
        self.credentials_tree.bind('<Double-1>', self.edit_credential)
        
        # Center the dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
    def refresh_list(self):
        """Refresh the treeview with current credentials."""
        self.credentials_tree.delete(*self.credentials_tree.get_children())
        for cred in self.credentials_list:
            self.credentials_tree.insert("", tk.END, values=(
                cred.get('description', 'No description'),
                cred.get('username', 'No username')
            ))
            
    def add_credential(self):
        """Add a new credential to the list."""
        dialog = CredentialDialog(self)
        self.wait_window(dialog)
        
        if dialog.result:
            self.credentials_list.append(dialog.result)
            self.refresh_list()
            
    def edit_credential(self, event=None):
        """Edit the selected credential."""
        selected = self.credentials_tree.selection()
        if selected:
            item = selected[0]
            index = self.credentials_tree.index(item)
            
            if 0 <= index < len(self.credentials_list):
                dialog = CredentialDialog(self, "Edit Credential", self.credentials_list[index])
                self.wait_window(dialog)
                
                if dialog.result:
                    self.credentials_list[index] = dialog.result
                    self.refresh_list()
                
    def remove_credential(self):
        """Remove the selected credential."""
        selected = self.credentials_tree.selection()
        if selected:
            item = selected[0]
            index = self.credentials_tree.index(item)
            
            if 0 <= index < len(self.credentials_list):
                if messagebox.askyesno("Confirm", "Are you sure you want to remove this credential?"):
                    del self.credentials_list[index]
                    self.refresh_list()
                
    def save(self):
        """Save the credentials list and close."""
        self.result = self.credentials_list.copy()
        self.destroy()
        
    def cancel(self):
        """Cancel and close without saving."""
        self.result = None
        self.destroy()


class CredentialSelector(tk.Toplevel):
    """
    Dialog for selecting a credential from the list.
    """
    
    def __init__(self, parent, credentials_list):
        """
        Initialize the credential selector.
        
        Args:
            parent: The parent window
            credentials_list: List of credentials to select from
        """
        super().__init__(parent)
        self.title("Select Credentials")
        self.geometry("500x300")
        self.configure(bg=Colors.BG_MAIN)
        self.transient(parent)
        self.grab_set()

        self.result = None
        self.parent = parent
        self.credentials_list = credentials_list

        # Main frame
        main_frame = ttk.Frame(self, padding=Spacing.MD)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(main_frame, text="Select credentials to use for this operation:").pack(padx=5, pady=5, anchor=tk.W)
        
        # Create Treeview for credentials
        columns = ("description", "username")
        self.credentials_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=10)
        self.credentials_tree.heading("description", text="Description")
        self.credentials_tree.heading("username", text="Username")
        
        self.credentials_tree.column("description", width=300)
        self.credentials_tree.column("username", width=150)
        
        self.credentials_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.credentials_tree.yview)
        self.credentials_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate list
        for i, cred in enumerate(credentials_list):
            self.credentials_tree.insert("", tk.END, values=(
                cred.get('description', 'No description'),
                cred.get('username', 'No username')
            ))
        
        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, padx=Spacing.SM, pady=Spacing.MD)

        ttk.Button(btn_frame, text="Select", command=self.select_credential,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=Spacing.SM)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel,
                   style="Secondary.TButton").pack(side=tk.LEFT, padx=Spacing.SM)
        ttk.Button(btn_frame, text="Use New Credentials", command=self.use_new,
                   style="Secondary.TButton").pack(side=tk.RIGHT, padx=Spacing.SM)
        
        # Bind double-click to select
        self.credentials_tree.bind('<Double-1>', lambda e: self.select_credential())
        
        # Center the dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
    def select_credential(self):
        """Select the highlighted credential."""
        selected = self.credentials_tree.selection()
        if selected:
            item = selected[0]
            index = self.credentials_tree.index(item)
            
            if 0 <= index < len(self.credentials_list):
                self.result = self.credentials_list[index]
                self.destroy()
        else:
            messagebox.showwarning("Warning", "Please select a credential from the list")
            
    def use_new(self):
        """Use a new credential just for this operation."""
        dialog = CredentialDialog(self)
        self.wait_window(dialog)
        
        if dialog.result:
            self.result = dialog.result
            self.destroy()
            
    def cancel(self):
        """Cancel selection."""
        self.result = None
        self.destroy()