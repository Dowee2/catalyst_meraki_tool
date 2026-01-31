"""
View for comparing interface statuses between Catalyst and Meraki switches.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import pandas as pd

from config.theme import Colors, Fonts, Spacing, configure_treeview_tags

class InterfaceCompareView:
    """
    View for comparing interface statuses between switches.
    """
    
    def __init__(self, parent_frame):
        """
        Initialize the interface comparison view.
        
        Args:
            parent_frame: The parent frame to place UI elements in
        """
        self.parent = parent_frame
        self.callbacks = {}
        
        # Create a paned window to allow resizing
        self.paned_window = ttk.PanedWindow(parent_frame, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=Spacing.MD, pady=Spacing.SM)
        
        # Create the input section (smaller)
        input_frame = ttk.LabelFrame(self.paned_window, text="Comparison Controls")
        self.paned_window.add(input_frame, weight=1)
        
        # Create the results section (larger)
        results_frame = ttk.LabelFrame(self.paned_window, text="Comparison Results")
        self.paned_window.add(results_frame, weight=3)  # Give more weight to results
        
        # Create the console section (smallest)
        console_frame = ttk.LabelFrame(self.paned_window, text="Output Console")
        self.paned_window.add(console_frame, weight=1)
        
        self.paned_window.update()
        window_height = self.paned_window.winfo_height()
        if window_height > 0:
            # Set input to 25%, results to 50%, console to 25%
            self.paned_window.sashpos(0, int(window_height * 0.25))
            self.paned_window.sashpos(1, int(window_height * 0.75))
        
        # Initialize sections
        self._create_input_section(input_frame)
        self._create_results_section(results_frame)
        self._create_console_section(console_frame)
        
        # Initialize data storage
        self.captures_data = []
        self.all_results = []

    def _create_input_section(self, parent_frame):
        """Create a more compact input section."""
        # Mode selection in a row
        mode_frame = ttk.Frame(parent_frame)
        mode_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.compare_mode = tk.StringVar(value="capture")
        ttk.Radiobutton(mode_frame, text="Capture Catalyst Data", variable=self.compare_mode, 
                    value="capture", command=self._toggle_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Compare with Meraki", 
                    variable=self.compare_mode, value="compare",
                    command=self._toggle_mode).pack(side=tk.LEFT, padx=5)
        
        # Container for Capture mode
        self.capture_frame = ttk.Frame(parent_frame)
        self.capture_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # More compact layout with grid
        ttk.Label(self.capture_frame, text="Catalyst Switch IP:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.catalyst_ip = ttk.Entry(self.capture_frame, width=20)
        self.catalyst_ip.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        
        # Credential and capture buttons in same row
        btn_frame = ttk.Frame(self.capture_frame)
        btn_frame.grid(row=0, column=2, padx=5, pady=2, sticky=tk.E)
        
        self.credential_button = ttk.Button(btn_frame, text="Credentials",
                                            width=10, style="Secondary.TButton")
        self.credential_button.pack(side=tk.LEFT, padx=Spacing.XS)

        self.capture_button = ttk.Button(btn_frame, text="Capture",
                                         width=10, style="Primary.TButton")
        self.capture_button.pack(side=tk.LEFT, padx=Spacing.XS)
        
        # Container for Compare mode - more compact
        self.compare_frame = ttk.Frame(parent_frame)
        self.compare_frame.pack(fill=tk.X, padx=5, pady=2)
        self.compare_frame.pack_forget()  # Hide initially
        
        # First row: capture selection and compare button
        ttk.Label(self.compare_frame, text="Select Captured Data:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.capture_combo = ttk.Combobox(self.compare_frame, width=40, state="readonly")
        self.capture_combo.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W+tk.E)
        
        # Second row: Meraki serials
        ttk.Label(self.compare_frame, text="Meraki Serial Numbers:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.meraki_serials_display = ttk.Entry(self.compare_frame, width=40, state="readonly")
        self.meraki_serials_display.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W+tk.E)
        
        # Action buttons in the same row
        compare_btn_frame = ttk.Frame(self.compare_frame)
        compare_btn_frame.grid(row=1, column=2, padx=5, pady=2, sticky=tk.E)
        
        self.serials_button = ttk.Button(compare_btn_frame, text="Serials",
                                         width=10, style="Secondary.TButton")
        self.serials_button.pack(side=tk.LEFT, padx=Spacing.XS)

        self.start_button = ttk.Button(compare_btn_frame, text="Compare",
                                       width=10, style="Primary.TButton")
        self.start_button.pack(side=tk.LEFT, padx=Spacing.XS)
        
    # In views/interface_compare_view.py and views/mac_compare_view.py - modify _create_results_section

    def _create_results_section(self, parent_frame):
        """Create the results section with treeview."""
        # Add a summary and controls bar at the top
        summary_frame = ttk.Frame(parent_frame)
        summary_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add a summary label
        self.summary_label = ttk.Label(summary_frame, text="No comparison performed yet")
        self.summary_label.pack(side=tk.LEFT, padx=5)
        
        # Add filtering options to the right of summary
        filter_frame = ttk.Frame(summary_frame)
        filter_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar(value="all")
        ttk.Radiobutton(filter_frame, text="All", variable=self.filter_var, value="all", command=self._apply_filter).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Matches Only", variable=self.filter_var, value="match", command=self._apply_filter).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Mismatches Only", variable=self.filter_var, value="mismatch", command=self._apply_filter).pack(side=tk.LEFT, padx=5)
        
        # Add export button
        ttk.Button(filter_frame, text="Export", command=self._export_results).pack(side=tk.LEFT, padx=5)
        
        # Create frame for treeview and scrollbars
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create Treeview for results
        columns = ("interface", "catalyst", "meraki", "match")  # Adjust columns as needed for MAC view
        self.results_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        self.results_tree.heading("interface", text="Catalyst Interface")
        self.results_tree.heading("catalyst", text="Catalyst Status")
        self.results_tree.heading("meraki", text="Meraki Status")
        self.results_tree.heading("match", text="Match")
        
        self.results_tree.column("interface", width=150)
        self.results_tree.column("catalyst", width=100)
        self.results_tree.column("meraki", width=100)
        self.results_tree.column("match", width=80)
        
        # Set up tag colors for matches/mismatches
        configure_treeview_tags(self.results_tree)

        # Add vertical scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=vsb.set)
        
        # Add horizontal scrollbar
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(xscrollcommand=hsb.set)
        
        # Grid layout for treeview and scrollbars
        self.results_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        # Configure grid weights
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

    def _apply_filter(self):
        """Apply the selected filter to the results."""
        filter_value = self.filter_var.get()
        
        # Store all results for filtering
        if not hasattr(self, 'all_results') or not self.all_results:
            return
            
        # Clear current display
        self.clear_results()
        
        # Apply filter
        for result in self.all_results:
            match_value = result.get('Match', False)
            
            # Skip based on filter
            if filter_value == "match" and not match_value:
                continue
            if filter_value == "mismatch" and match_value:
                continue
                
            # Add to treeview with color tag
            tag = 'match' if match_value else 'mismatch'
            self.results_tree.insert("", tk.END, values=(
                result.get('Catalyst_Interface', ''),
                result.get('Catalyst_Status', ''),
                result.get('Meraki_Status', ''),
                "Yes" if match_value else "No"
            ), tags=(tag,))
            
    def _export_results(self):
        """Export results to a CSV file."""
        if not hasattr(self, 'all_results') or not self.all_results:
            messagebox.showinfo("Export", "No results to export")
            return
            
        # Ask for file location
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Results"
        )
        
        if not filename:
            return
            
        # Export to CSV
        
        df = pd.DataFrame(self.all_results)
        df.to_csv(filename, index=False)
        
        messagebox.showinfo("Export", f"Results exported to {filename}")
    
    def _toggle_mode(self):
        """Toggle between capture and compare modes."""
        mode = self.compare_mode.get()
        if mode == "capture":
            self.compare_frame.pack_forget()
            self.capture_frame.pack(fill=tk.X, padx=5, pady=5)
        else:  # mode == "compare"
            self.capture_frame.pack_forget()
            self.compare_frame.pack(fill=tk.X, padx=5, pady=5)
            
    def set_mode(self, mode):
        """
        Set the view mode (capture or compare).
        
        Args:
            mode (str): Either "capture" or "compare"
        """
        if mode not in ["capture", "compare"]:
            return
            
        # Update the radio button selection
        self.compare_mode.set(mode)
        
        # Toggle the visibility of frames
        if mode == "capture":
            self.compare_frame.pack_forget()
            self.capture_frame.pack(fill=tk.X, padx=5, pady=5)
        else:  # mode == "compare"
            self.capture_frame.pack_forget()
            self.compare_frame.pack(fill=tk.X, padx=5, pady=5)

    def _create_console_section(self, parent_frame):
        """Create a smaller console output section."""
        # Create a frame for the console with a fixed height
        console_container = ttk.Frame(parent_frame)
        console_container.pack(fill=tk.BOTH, expand=True)

        # Create the console with a smaller default height
        self.console = scrolledtext.ScrolledText(
            console_container, wrap=tk.WORD, height=6,
            font=Fonts.SMALL, bg=Colors.BG_CARD, fg=Colors.TEXT_PRIMARY,
            insertbackground=Colors.PRIMARY)
        self.console.pack(fill=tk.BOTH, expand=True, padx=Spacing.SM, pady=Spacing.SM)
        
    
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
    
    def clear_results(self):
        """Clear the results treeview."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
    
    def add_result(self, interface, catalyst_status, meraki_status, match):
        """
        Add a result to the treeview.
        
        Args:
            interface (str): The Catalyst interface name
            catalyst_status (str): The Catalyst interface status
            meraki_status (str): The Meraki port status
            match (bool): Whether the statuses match
        """
        match_value = "Yes" if match else "No"
        self.results_tree.insert("", tk.END, values=(
            interface,
            catalyst_status,
            meraki_status,
            match_value
        ))
    
    def set_results(self, results):
        """
        Set all results at once.
        
        Args:
            results (list): List of result dictionaries
        """
        # Store all results for filtering
        self.all_results = results
        
        # Clear current display
        self.clear_results()
        
        # Count matches/mismatches
        match_count = sum(1 for result in results if result.get('Match', False))
        mismatch_count = len(results) - match_count
        
        # Update summary
        self.summary_label.config(
            text=f"Results: {len(results)} interfaces, {match_count} matches, {mismatch_count} mismatches"
        )
        
        # Apply current filter
        self._apply_filter()

        # Set up tag colors for matches/mismatches
        configure_treeview_tags(self.results_tree)
            
    
    def set_capture_options(self, options, captures_data):
        """
        Set the options for the capture dropdown.
        
        Args:
            options (list): List of string options to display
            captures_data (list): List of capture metadata dictionaries
        """
        self.capture_combo['values'] = options
        self.captures_data = captures_data  # Store the full capture data
        
        # Select the first option if available
        if options:
            self.capture_combo.current(0)
    
    def set_callback(self, event_name, callback):
        """
        Set a callback function for a UI event.
        
        Args:
            event_name (str): The event name
            callback: The callback function
        """
        self.callbacks[event_name] = callback
        
        # Connect callbacks to UI elements
        if event_name == "start_comparison":
            self.start_button.config(command=callback)
        elif event_name == "manage_credentials":
            self.credential_button.config(command=callback)
        elif event_name == "manage_serials":
            self.serials_button.config(command=callback)
        elif event_name == "capture_interfaces":
            self.capture_button.config(command=callback)
    
    def on_tab_selected(self):
        """Handle tab selection event."""
        # Update any UI elements as needed when tab is selected
        pass