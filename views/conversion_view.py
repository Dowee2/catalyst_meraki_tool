"""
View for the Convert Config tab.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog

from config.theme import Colors, Fonts, Spacing

class ConversionView:
    """
    View for converting Catalyst switch configurations to Meraki.
    """
    
    def __init__(self, parent_frame):
        """
        Initialize the conversion view.
        
        Args:
            parent_frame: The parent frame to place UI elements in
        """
        self.parent = parent_frame
        self.callbacks = {}
        
        # Frame for switch inputs
        self._create_input_section()
        
        # Output console
        self._create_console_section()
    
    def _create_input_section(self):
        """Create the input section UI components."""
        input_frame = ttk.LabelFrame(self.parent, text="Switch Information")
        input_frame.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD, ipady=Spacing.SM)
        
        # Source selection (IP vs. File)
        source_frame = ttk.Frame(input_frame)
        source_frame.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        self.config_source = tk.StringVar(value="ip")
        ttk.Radiobutton(source_frame, text="Connect to Switch IP", variable=self.config_source, 
                       value="ip", command=self._on_source_changed).grid(row=0, column=0, padx=5, sticky=tk.W)
        ttk.Radiobutton(source_frame, text="Load Running Config File", variable=self.config_source, 
                       value="file", command=self._on_source_changed).grid(row=0, column=1, padx=5, sticky=tk.W)
        
        # IP Source Container (shown by default)
        self.ip_container = ttk.Frame(input_frame)
        self.ip_container.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Catalyst IP address
        ttk.Label(self.ip_container, text="Catalyst Switch IP:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.catalyst_ip = ttk.Entry(self.ip_container, width=20)
        self.catalyst_ip.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Credential management button
        self.credential_button = ttk.Button(self.ip_container, text="Configure Credentials",
                                            style="Secondary.TButton")
        self.credential_button.grid(row=0, column=2, padx=Spacing.SM, pady=Spacing.SM, sticky=tk.W)
        
        # File Source Container (hidden initially)
        self.file_container = ttk.Frame(input_frame)
        self.file_container.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        self.file_container.grid_remove()  # Hide initially
        
        # File selection controls
        ttk.Label(self.file_container, text="Config File:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.config_file_path = ttk.Entry(self.file_container, width=40)
        self.config_file_path.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        self.browse_button = ttk.Button(self.file_container, text="Browse...",
                                        style="Secondary.TButton")
        self.browse_button.grid(row=0, column=2, padx=Spacing.SM, pady=Spacing.SM, sticky=tk.W)
        
        ttk.Label(self.file_container, text="Switch Hostname:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.config_hostname = ttk.Entry(self.file_container, width=20)
        self.config_hostname.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Meraki Serial Numbers (common for both sources)
        ttk.Label(input_frame, text="Meraki Serial Numbers:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.meraki_serials_display = ttk.Entry(input_frame, width=40, state="readonly")
        self.meraki_serials_display.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        self.serials_button = ttk.Button(input_frame, text="Manage Serials",
                                         style="Secondary.TButton")
        self.serials_button.grid(row=2, column=2, padx=Spacing.SM, pady=Spacing.SM, sticky=tk.W)
        
        # Switch type selection (3850 or 2960)
        self.switch_type = tk.StringVar(value="2960")
        ttk.Radiobutton(input_frame, text="Catalyst 2960 Series", variable=self.switch_type, value="2960").grid(
            row=3, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(input_frame, text="Catalyst 3850 Series", variable=self.switch_type, value="3850").grid(
            row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Button to start conversion
        btn_frame = ttk.Frame(self.parent)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_button = ttk.Button(btn_frame, text="Start Conversion",
                                       style="Primary.TButton")
        self.start_button.pack(side=tk.LEFT, pady=Spacing.MD, padx=Spacing.SM)
    
    def _create_console_section(self):
        """Create the console output section."""
        console_frame = ttk.LabelFrame(self.parent, text="Output Console")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=Spacing.MD, pady=Spacing.MD)

        self.console = scrolledtext.ScrolledText(
            console_frame, wrap=tk.WORD,
            font=Fonts.SMALL, bg=Colors.BG_CARD, fg=Colors.TEXT_PRIMARY,
            insertbackground=Colors.PRIMARY)
        self.console.pack(fill=tk.BOTH, expand=True, padx=Spacing.SM, pady=Spacing.SM)
    
    def _on_source_changed(self):
        """Handle source radio button changes."""
        source = self.config_source.get()
        if source == "ip":
            self.file_container.grid_remove()
            self.ip_container.grid()
        else:  # source == "file"
            self.ip_container.grid_remove()
            self.file_container.grid()
    
    def clear_console(self):
        """Clear the console output."""
        self.console.delete("1.0", tk.END)
    
    def append_console(self, text):
        """
        Append text to the console output.
        
        Args:
            text (str): The text to append
        """
        self.console.insert(tk.END, text)
        self.console.see(tk.END)  # Scroll to the end
    
    def get_ip_address(self):
        """
        Get the entered Catalyst IP address.
        
        Returns:
            str: The IP address
        """
        return self.catalyst_ip.get().strip()
    
    def get_config_file_path(self):
        """
        Get the selected config file path.
        
        Returns:
            str: The file path
        """
        return self.config_file_path.get().strip()
    
    def get_hostname(self):
        """
        Get the entered hostname.
        
        Returns:
            str: The hostname
        """
        return self.config_hostname.get().strip()
    
    def get_switch_type(self):
        """
        Get the selected switch type.
        
        Returns:
            str: "2960" or "3850"
        """
        return self.switch_type.get()
    
    def get_source_type(self):
        """
        Get the selected source type.
        
        Returns:
            str: "ip" or "file"
        """
        return self.config_source.get()
    
    def set_serials_display(self, serials):
        """
        Set the serials display text.
        
        Args:
            serials (list): List of serial numbers
        """
        self.meraki_serials_display.config(state="normal")
        self.meraki_serials_display.delete(0, tk.END)
        self.meraki_serials_display.insert(0, ", ".join(serials) if serials else "")
        self.meraki_serials_display.config(state="readonly")
    
    def set_callback(self, event_name, callback):
        """
        Set a callback function for a UI event.
        
        Args:
            event_name (str): The event name
            callback: The callback function
        """
        self.callbacks[event_name] = callback
        
        # Connect callbacks to UI elements
        if event_name == "start_conversion":
            self.start_button.config(command=callback)
        elif event_name == "manage_credentials":
            self.credential_button.config(command=callback)
        elif event_name == "manage_serials":
            self.serials_button.config(command=callback)
        elif event_name == "browse_config":
            self.browse_button.config(command=callback)
    
    def on_tab_selected(self):
        """Handle tab selection event."""
        # Update any UI elements as needed when tab is selected
        pass
    
    def show_file_dialog(self, title="Select File", filetypes=None):
        """
        Show a file selection dialog.
        
        Args:
            title (str): The dialog title
            filetypes (list): List of file type tuples
            
        Returns:
            str: The selected file path or empty string if cancelled
        """
        if filetypes is None:
            filetypes = [("Text files", "*.txt"), ("All files", "*.*")]
            
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=filetypes
        )
        
        if file_path:
            self.config_file_path.delete(0, tk.END)
            self.config_file_path.insert(0, file_path)
            
        return file_path