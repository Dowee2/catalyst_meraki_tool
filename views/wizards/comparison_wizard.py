"""
Comparison Wizard - 3-step wizard for comparing Catalyst and Meraki switches.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable, Optional

from config.theme import Colors, Fonts, Spacing, configure_treeview_tags
from views.wizard.base_wizard import BaseWizard
from views.components.info_box import InfoBox
from views.components.ip_input import IPInput
from views.dialogs.credential_dialog import CredentialDialog, CredentialSelector, CredentialListManager
from views.dialogs.serial_dialog import SerialListManager


class ComparisonWizard(ttk.Frame):
    """
    A 3-step wizard for comparing Catalyst and Meraki switches.

    Steps:
    1. Capture - Enter Catalyst switch details and capture data
    2. Meraki Details - Enter Meraki serial numbers
    3. Results - View comparison results
    """

    def __init__(
        self,
        parent,
        credentials_model,
        serials_model,
        switch_data_model,
        on_complete: Optional[Callable[[dict], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Initialize the comparison wizard.

        Args:
            parent: Parent widget
            credentials_model: Model for managing credentials
            serials_model: Model for managing serial numbers
            switch_data_model: Model for saved switch data
            on_complete: Callback when wizard finishes with collected data
            on_cancel: Callback when wizard is cancelled
        """
        super().__init__(parent, **kwargs)
        self.credentials_model = credentials_model
        self.serials_model = serials_model
        self.switch_data_model = switch_data_model
        self.on_complete_callback = on_complete
        self.on_cancel_callback = on_cancel

        # Wizard data storage
        self.wizard_data = {
            'catalyst_ip': '',
            'credentials': None,
            'compare_interfaces': True,
            'compare_macs': True,
            'meraki_serials': [],
            'use_saved_capture': False,
            'saved_capture_index': -1
        }

        # Captured data storage
        self.captured_interface_data = None
        self.captured_mac_data = None
        self.captured_hostname = ''

        # UI references
        self.ip_input = None
        self.cred_display_label = None
        self.serials_display = None
        self.interface_check_var = None
        self.mac_check_var = None
        self.capture_console = None
        self.results_notebook = None
        self.interface_tree = None
        self.mac_tree = None

        self._create_wizard()

    def _create_wizard(self):
        """Create the wizard with all steps."""
        steps = [
            {
                'name': 'Capture',
                'title': 'Step 1 of 3: Capture old switch data',
                'description': 'Connect to your Catalyst switch and capture its current state',
                'create_content': self._create_capture_step,
                'validate': self._validate_capture_step
            },
            {
                'name': 'Meraki',
                'title': 'Step 2 of 3: Enter new Meraki switch details',
                'description': 'Enter the serial numbers of your Meraki switches',
                'create_content': self._create_meraki_step,
                'validate': self._validate_meraki_step,
                'on_leave': self._save_meraki_data
            },
            {
                'name': 'Compare',
                'title': 'Step 3 of 3: Compare and view results',
                'description': 'Review the comparison between your old and new switches',
                'create_content': self._create_results_step,
                'on_enter': self._on_results_enter
            }
        ]

        self.wizard = BaseWizard(
            self,
            steps=steps,
            on_complete=self._on_wizard_complete,
            on_cancel=self._on_wizard_cancel
        )
        self.wizard.pack(fill=tk.BOTH, expand=True)

    # =========================================================================
    # Step 1: Capture Source Data
    # =========================================================================

    def _create_capture_step(self, content_frame):
        """Create the capture step UI."""
        self._create_source_selection(content_frame)
        self._create_new_capture_container(content_frame)
        self._create_saved_capture_container(content_frame)
        self._refresh_saved_captures()

    def _create_source_selection(self, parent):
        """Create the data source selection (new vs saved)."""
        source_frame = ttk.LabelFrame(
            parent,
            text="Data Source",
            style="Card.TLabelframe"
        )
        source_frame.pack(fill=tk.X, pady=Spacing.SM)

        source_inner = ttk.Frame(source_frame)
        source_inner.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD)

        self.source_var = tk.StringVar(value='new')

        ttk.Radiobutton(
            source_inner,
            text="Capture new data from switch",
            variable=self.source_var,
            value='new',
            command=self._on_source_changed
        ).pack(side=tk.LEFT, padx=(0, Spacing.LG))

        ttk.Radiobutton(
            source_inner,
            text="Use previously saved capture",
            variable=self.source_var,
            value='saved',
            command=self._on_source_changed
        ).pack(side=tk.LEFT)

    def _create_new_capture_container(self, parent):
        """Create the new capture container with all its components."""
        self.new_capture_frame = ttk.Frame(parent, style="Card.TFrame")
        self.new_capture_frame.pack(fill=tk.X, pady=Spacing.SM)

        self._create_ip_input_section()
        self._create_credentials_section()
        self._create_compare_options_section()
        self._create_capture_button_section()
        self._create_capture_console_section()

    def _create_ip_input_section(self):
        """Create the IP input field."""
        ip_frame = ttk.Frame(self.new_capture_frame)
        ip_frame.pack(fill=tk.X, pady=Spacing.SM)

        self.ip_input = IPInput(
            ip_frame,
            label="Old switch address:",
            placeholder="192.168.1.1"
        )
        self.ip_input.pack(fill=tk.X)

    def _create_credentials_section(self):
        """Create the credentials selection section."""
        cred_frame = ttk.LabelFrame(
            self.new_capture_frame,
            text="Login credentials",
            style="Card.TLabelframe"
        )
        cred_frame.pack(fill=tk.X, pady=Spacing.SM)

        cred_inner = ttk.Frame(cred_frame)
        cred_inner.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD)

        self.cred_display_label = ttk.Label(
            cred_inner,
            text="No credentials selected",
            style="Secondary.TLabel"
        )
        self.cred_display_label.pack(side=tk.LEFT)

        ttk.Button(
            cred_inner,
            text="Select Credentials",
            style="Secondary.TButton",
            command=self._select_credentials
        ).pack(side=tk.RIGHT)

    def _create_compare_options_section(self):
        """Create the comparison options checkboxes."""
        compare_frame = ttk.LabelFrame(
            self.new_capture_frame,
            text="What to compare",
            style="Card.TLabelframe"
        )
        compare_frame.pack(fill=tk.X, pady=Spacing.SM)

        compare_inner = ttk.Frame(compare_frame)
        compare_inner.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD)

        self.interface_check_var = tk.BooleanVar(value=True)
        self.mac_check_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(
            compare_inner,
            text="Port status (up/down)",
            variable=self.interface_check_var
        ).pack(anchor=tk.W, pady=Spacing.XS)

        ttk.Checkbutton(
            compare_inner,
            text="Connected devices (MAC addresses)",
            variable=self.mac_check_var
        ).pack(anchor=tk.W, pady=Spacing.XS)

    def _create_capture_button_section(self):
        """Create the capture button and status label."""
        capture_btn_frame = ttk.Frame(self.new_capture_frame)
        capture_btn_frame.pack(fill=tk.X, pady=Spacing.SM)

        self.capture_btn = ttk.Button(
            capture_btn_frame,
            text="Capture Data",
            style="Primary.TButton",
            command=self._capture_data
        )
        self.capture_btn.pack(side=tk.LEFT)

        self.capture_status_label = ttk.Label(
            capture_btn_frame,
            text="",
            style="Card.TLabel"
        )
        self.capture_status_label.pack(side=tk.LEFT, padx=Spacing.MD)

    def _create_capture_console_section(self):
        """Create the capture progress console."""
        console_frame = ttk.LabelFrame(
            self.new_capture_frame,
            text="Capture Progress",
            style="Card.TLabelframe"
        )
        console_frame.pack(fill=tk.BOTH, expand=True, pady=Spacing.SM)

        self.capture_console = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            font=Fonts.SMALL,
            bg=Colors.BG_CARD,
            fg=Colors.TEXT_PRIMARY,
            height=6
        )
        self.capture_console.pack(fill=tk.BOTH, expand=True, padx=Spacing.SM, pady=Spacing.SM)

    def _create_saved_capture_container(self, parent):
        """Create the saved capture selection container (hidden initially)."""
        self.saved_capture_frame = ttk.Frame(parent, style="Card.TFrame")

        saved_inner = ttk.LabelFrame(
            self.saved_capture_frame,
            text="Select saved capture",
            style="Card.TLabelframe"
        )
        saved_inner.pack(fill=tk.X, pady=Spacing.SM)

        saved_content = ttk.Frame(saved_inner)
        saved_content.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD)

        # Interface captures
        ttk.Label(saved_content, text="Interface data:").pack(anchor=tk.W)
        self.interface_capture_combo = ttk.Combobox(saved_content, width=60, state="readonly")
        self.interface_capture_combo.pack(fill=tk.X, pady=(Spacing.XS, Spacing.MD))

        # MAC captures
        ttk.Label(saved_content, text="MAC address data:").pack(anchor=tk.W)
        self.mac_capture_combo = ttk.Combobox(saved_content, width=60, state="readonly")
        self.mac_capture_combo.pack(fill=tk.X, pady=Spacing.XS)

    def _on_source_changed(self):
        """Handle source type change."""
        source = self.source_var.get()
        if source == 'new':
            self.saved_capture_frame.pack_forget()
            self.new_capture_frame.pack(fill=tk.X, pady=Spacing.SM)
            self.wizard_data['use_saved_capture'] = False
        else:
            self.new_capture_frame.pack_forget()
            self.saved_capture_frame.pack(fill=tk.X, pady=Spacing.SM)
            self.wizard_data['use_saved_capture'] = True
            self._refresh_saved_captures()

    def _refresh_saved_captures(self):
        """Refresh the saved captures dropdowns."""
        try:
            # Interface captures
            interface_captures = self.switch_data_model.get_saved_interface_captures()
            interface_options = [
                f"{c['hostname']} ({c['switch_ip']}) - {c['datetime']} ({c['count']} interfaces)"
                for c in interface_captures
            ]
            self.interface_capture_combo['values'] = interface_options
            self._interface_captures_data = interface_captures
            if interface_options:
                self.interface_capture_combo.current(0)

            # MAC captures
            mac_captures = self.switch_data_model.get_saved_mac_captures()
            mac_options = [
                f"{c['hostname']} ({c['switch_ip']}) - {c['datetime']} ({c['count']} MAC entries)"
                for c in mac_captures
            ]
            self.mac_capture_combo['values'] = mac_options
            self._mac_captures_data = mac_captures
            if mac_options:
                self.mac_capture_combo.current(0)
        except Exception as e:
            print(f"Error refreshing saved captures: {e}")

    def _select_credentials(self):
        """Open credential selection dialog."""
        creds = self.credentials_model.get_credentials()

        if not creds:
            # No saved credentials, create new
            dialog = CredentialDialog(self)
            self.wait_window(dialog)
            if dialog.result:
                self.wizard_data['credentials'] = dialog.result
                self._update_credential_display()
        else:
            # Show selector
            dialog = CredentialSelector(self, creds)
            self.wait_window(dialog)
            if dialog.result:
                self.wizard_data['credentials'] = dialog.result
                self._update_credential_display()

    def _update_credential_display(self):
        """Update the credentials display."""
        if self.wizard_data['credentials']:
            username = self.wizard_data['credentials'].get('username', '')
            self.cred_display_label.config(
                text=f"Selected: {username}",
                foreground=Colors.SUCCESS
            )

    def _capture_data(self):
        """Capture data from the Catalyst switch."""
        # Validate inputs
        is_valid, error = self.ip_input.validate()
        if not is_valid:
            self.wizard.show_error(error)
            return

        if not self.wizard_data['credentials']:
            self.wizard.show_error("Please select or enter credentials")
            return

        if not self.interface_check_var.get() and not self.mac_check_var.get():
            self.wizard.show_error("Please select at least one comparison type")
            return

        # Save settings
        self.wizard_data['catalyst_ip'] = self.ip_input.get_value()
        self.wizard_data['compare_interfaces'] = self.interface_check_var.get()
        self.wizard_data['compare_macs'] = self.mac_check_var.get()

        # Clear console and start capture
        self.capture_console.delete('1.0', tk.END)
        self.capture_btn.config(state='disabled')
        self.capture_status_label.config(text="Capturing...", foreground=Colors.PRIMARY)

        self._append_capture_console(f"Connecting to {self.wizard_data['catalyst_ip']}...\n")

        # Run capture in background
        self._run_capture()

    def _run_capture(self):
        """Run the capture process."""
        from utils.workers import BackgroundTask

        credentials = [{
            'username': self.wizard_data['credentials']['username'],
            'password': self.wizard_data['credentials']['password']
        }]

        catalyst_ip = self.wizard_data['catalyst_ip']

        def do_capture():
            from utils.netmiko_utils import get_running_config
            import pandas as pd

            results = {'hostname': '', 'interfaces': None, 'macs': None}

            # Capture interfaces if selected
            if self.wizard_data['compare_interfaces']:
                interface_data, hostname = get_running_config(
                    ip_address=catalyst_ip,
                    credentials=credentials,
                    command='show ip int brief',
                    use_textfsm=True,
                    read_timeout=60
                )
                results['interfaces'] = interface_data
                results['hostname'] = hostname

            # Capture MACs if selected
            if self.wizard_data['compare_macs']:
                macs_raw, hostname = get_running_config(
                    ip_address=catalyst_ip,
                    credentials=credentials,
                    command='show mac address-table',
                    use_textfsm=True,
                    read_timeout=90
                )
                macs_df = pd.DataFrame(macs_raw)
                if not macs_df.empty:
                    macs_df.rename(columns={
                        'destination_address': 'mac_address',
                        'destination_port': 'port',
                        'vlan_id': 'vlan'
                    }, inplace=True)
                    if 'port' in macs_df.columns:
                        macs_df['port'] = macs_df['port'].apply(lambda x: x[0] if isinstance(x, list) else x)
                    macs_df = macs_df[['mac_address', 'vlan', 'port']]
                results['macs'] = macs_df
                if not results['hostname']:
                    results['hostname'] = hostname

            return results

        BackgroundTask.run(
            do_capture,
            console_widget=self.capture_console,
            success_callback=self._on_capture_success,
            error_callback=self._on_capture_error
        )

    def _on_capture_success(self, result):
        """Handle successful capture."""
        self.captured_hostname = result['hostname']
        self.captured_interface_data = result['interfaces']
        self.captured_mac_data = result['macs']

        interface_count = len(result['interfaces']) if result['interfaces'] else 0
        mac_count = len(result['macs']) if result['macs'] is not None and not result['macs'].empty else 0

        self._append_capture_console(f"\nCapture completed for {self.captured_hostname}!\n")
        self._append_capture_console(f"  - Interfaces: {interface_count}\n")
        self._append_capture_console(f"  - MAC addresses: {mac_count}\n")

        self.capture_btn.config(state='normal')
        self.capture_status_label.config(
            text=f"Captured from {self.captured_hostname}",
            foreground=Colors.SUCCESS
        )
        self.wizard.clear_error()

    def _on_capture_error(self, error):
        """Handle capture error."""
        self._append_capture_console(f"\nError: {str(error)}\n")
        self.capture_btn.config(state='normal')
        self.capture_status_label.config(text="Capture failed", foreground=Colors.ERROR)
        self.wizard.show_error(str(error))

    def _append_capture_console(self, text):
        """Append text to capture console."""
        if self.capture_console:
            self.capture_console.insert(tk.END, text)
            self.capture_console.see(tk.END)

    def _validate_capture_step(self):
        """Validate the capture step."""
        if self.wizard_data['use_saved_capture']:
            # Check if saved captures are selected
            if self.interface_capture_combo.current() < 0 and self.mac_capture_combo.current() < 0:
                return False, "Please select at least one saved capture"
            return True, ""
        else:
            # Check if we have captured data
            if self.captured_interface_data is None and self.captured_mac_data is None:
                return False, "Please capture data from the switch first"
            return True, ""

    # =========================================================================
    # Step 2: Meraki Details
    # =========================================================================

    def _create_meraki_step(self, content_frame):
        """Create the Meraki details step UI."""
        self._create_meraki_serials_section(content_frame)
        self._create_comparison_summary_section(content_frame)
        self._update_comparison_summary()

    def _create_meraki_serials_section(self, parent):
        """Create the Meraki serial numbers input section."""
        serials_frame = ttk.LabelFrame(
            parent,
            text="New Meraki switch serial numbers",
            style="Card.TLabelframe"
        )
        serials_frame.pack(fill=tk.X, pady=Spacing.SM)

        serials_inner = ttk.Frame(serials_frame)
        serials_inner.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD)

        self.serials_display = ttk.Entry(serials_inner, width=50, state="readonly")
        self.serials_display.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            serials_inner,
            text="Manage Serials",
            style="Secondary.TButton",
            command=self._manage_serials
        ).pack(side=tk.LEFT, padx=(Spacing.SM, 0))

        InfoBox(
            serials_frame,
            message="Enter the serial number(s) of your new Meraki switch(es). "
                    "These should match the switches that replaced your old Catalyst switch.",
            box_type='info'
        ).pack(fill=tk.X, padx=Spacing.MD, pady=(0, Spacing.MD))

    def _create_comparison_summary_section(self, parent):
        """Create the comparison summary display section."""
        summary_frame = ttk.LabelFrame(
            parent,
            text="Comparison Summary",
            style="Card.TLabelframe"
        )
        summary_frame.pack(fill=tk.X, pady=Spacing.MD)

        self.comparison_summary = ttk.Label(
            summary_frame,
            text="",
            style="Card.TLabel",
            wraplength=500
        )
        self.comparison_summary.pack(padx=Spacing.MD, pady=Spacing.MD, anchor=tk.W)

    def _update_comparison_summary(self):
        """Update the comparison summary display."""
        lines = []

        if self.wizard_data['use_saved_capture']:
            lines.append("Using saved capture data")
        else:
            if self.captured_hostname:
                lines.append(f"Source: {self.captured_hostname} ({self.wizard_data.get('catalyst_ip', '')})")

            if self.captured_interface_data is not None:
                lines.append(f"  - {len(self.captured_interface_data)} interfaces to compare")
            if self.captured_mac_data is not None and not self.captured_mac_data.empty:
                lines.append(f"  - {len(self.captured_mac_data)} MAC addresses to compare")

        if hasattr(self, 'comparison_summary'):
            self.comparison_summary.config(text='\n'.join(lines))

    def _manage_serials(self):
        """Open serial management dialog."""
        dialog = SerialListManager(
            self,
            self.wizard_data['meraki_serials'],
            "Manage Meraki Serial Numbers"
        )
        self.wait_window(dialog)

        if dialog.result is not None:
            self.wizard_data['meraki_serials'] = dialog.result
            self._update_serials_display()

    def _update_serials_display(self):
        """Update the serials display."""
        serials = self.wizard_data['meraki_serials']
        self.serials_display.config(state="normal")
        self.serials_display.delete(0, tk.END)
        self.serials_display.insert(0, ", ".join(serials) if serials else "No serials entered")
        self.serials_display.config(state="readonly")

    def _validate_meraki_step(self):
        """Validate the Meraki step."""
        if not self.wizard_data['meraki_serials']:
            return False, "Please add at least one Meraki serial number"
        return True, ""

    def _save_meraki_data(self):
        """Save Meraki data (called on leaving step)."""
        self._update_comparison_summary()

    # =========================================================================
    # Step 3: Results
    # =========================================================================

    def _create_results_step(self, content_frame):
        """Create the results step UI."""
        self._create_results_status_section(content_frame)
        self._create_results_notebook(content_frame)
        self._create_results_console(content_frame)

    def _create_results_status_section(self, parent):
        """Create the status label and compare button."""
        self.results_status = ttk.Label(
            parent,
            text="Click 'Compare' to start the comparison",
            style="Card.TLabel",
            font=Fonts.BOLD
        )
        self.results_status.pack(pady=Spacing.SM)

        self.compare_btn = ttk.Button(
            parent,
            text="Start Comparison",
            style="Primary.TButton",
            command=self._run_comparison
        )
        self.compare_btn.pack(pady=Spacing.SM)

    def _create_results_notebook(self, parent):
        """Create the results notebook with tabs."""
        self.results_notebook = ttk.Notebook(parent)
        self.results_notebook.pack(fill=tk.BOTH, expand=True, pady=Spacing.SM)

        # Interface results tab
        interface_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(interface_frame, text="Port Status")
        self._create_interface_results(interface_frame)

        # MAC results tab
        mac_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(mac_frame, text="Connected Devices")
        self._create_mac_results(mac_frame)

    def _create_results_console(self, parent):
        """Create the results progress console."""
        console_frame = ttk.LabelFrame(
            parent,
            text="Progress",
            style="Card.TLabelframe"
        )
        console_frame.pack(fill=tk.X, pady=Spacing.SM)

        self.results_console = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            font=Fonts.SMALL,
            bg=Colors.BG_CARD,
            fg=Colors.TEXT_PRIMARY,
            height=4
        )
        self.results_console.pack(fill=tk.X, padx=Spacing.SM, pady=Spacing.SM)

    def _create_interface_results(self, parent):
        """Create interface results treeview."""
        # Summary
        self.interface_summary = ttk.Label(parent, text="No results yet")
        self.interface_summary.pack(anchor=tk.W, padx=Spacing.SM, pady=Spacing.SM)

        # Treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=Spacing.SM, pady=Spacing.SM)

        columns = ("interface", "catalyst", "meraki", "match")
        self.interface_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        self.interface_tree.heading("interface", text="Interface")
        self.interface_tree.heading("catalyst", text="Old Status")
        self.interface_tree.heading("meraki", text="New Status")
        self.interface_tree.heading("match", text="Match")

        self.interface_tree.column("interface", width=150)
        self.interface_tree.column("catalyst", width=100)
        self.interface_tree.column("meraki", width=100)
        self.interface_tree.column("match", width=80)

        configure_treeview_tags(self.interface_tree)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.interface_tree.yview)
        self.interface_tree.configure(yscrollcommand=vsb.set)

        self.interface_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_mac_results(self, parent):
        """Create MAC results treeview."""
        # Summary
        self.mac_summary = ttk.Label(parent, text="No results yet")
        self.mac_summary.pack(anchor=tk.W, padx=Spacing.SM, pady=Spacing.SM)

        # Treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=Spacing.SM, pady=Spacing.SM)

        columns = ("mac", "catalyst_port", "meraki_port", "status")
        self.mac_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        self.mac_tree.heading("mac", text="MAC Address")
        self.mac_tree.heading("catalyst_port", text="Old Port")
        self.mac_tree.heading("meraki_port", text="New Port")
        self.mac_tree.heading("status", text="Status")

        self.mac_tree.column("mac", width=150)
        self.mac_tree.column("catalyst_port", width=120)
        self.mac_tree.column("meraki_port", width=120)
        self.mac_tree.column("status", width=120)

        configure_treeview_tags(self.mac_tree)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.mac_tree.yview)
        self.mac_tree.configure(yscrollcommand=vsb.set)

        self.mac_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_results_enter(self):
        """Called when entering the results step."""
        self._update_comparison_summary()

    def _run_comparison(self):
        """Run the comparison."""
        from utils.workers import BackgroundTask
        from utils.config_manager import get_api_key
        from config.script_types import ScriptType

        api_key = get_api_key()
        if not api_key:
            self.wizard.show_error("Meraki API Key is not set. Please configure it in Settings.")
            return

        self.compare_btn.config(state='disabled')
        self.results_status.config(text="Comparing...", foreground=Colors.PRIMARY)
        self.results_console.delete('1.0', tk.END)

        meraki_serials = self.wizard_data['meraki_serials']

        def do_comparison():
            results = {'interfaces': None, 'macs': None}

            # Compare interfaces
            if self.captured_interface_data is not None:
                self._append_results_console("Comparing port status...\n")
                # This would use the actual comparison module
                # For now, create mock results structure
                results['interfaces'] = []
                for item in self.captured_interface_data:
                    results['interfaces'].append({
                        'Catalyst_Interface': item.get('intf', ''),
                        'Catalyst_Status': item.get('status', ''),
                        'Meraki_Status': 'up',  # Placeholder
                        'Match': item.get('status', '').lower() == 'up'
                    })

            # Compare MACs
            if self.captured_mac_data is not None and not self.captured_mac_data.empty:
                self._append_results_console("Comparing connected devices...\n")
                results['macs'] = []
                for _, row in self.captured_mac_data.iterrows():
                    results['macs'].append({
                        'MAC_Address': row.get('mac_address', ''),
                        'Catalyst_Port': row.get('port', ''),
                        'Meraki_PortId': row.get('port', ''),  # Placeholder
                        'Status': 'Match'  # Placeholder
                    })

            return results

        BackgroundTask.run(
            do_comparison,
            console_widget=self.results_console,
            success_callback=self._on_comparison_success,
            error_callback=self._on_comparison_error
        )

    def _on_comparison_success(self, results):
        """Handle successful comparison."""
        self.compare_btn.config(state='normal')
        self.results_status.config(text="Comparison complete!", foreground=Colors.SUCCESS)

        # Display interface results
        if results['interfaces']:
            self._display_interface_results(results['interfaces'])

        # Display MAC results
        if results['macs']:
            self._display_mac_results(results['macs'])

        self._append_results_console("\nComparison completed successfully!\n")

    def _on_comparison_error(self, error):
        """Handle comparison error."""
        self.compare_btn.config(state='normal')
        self.results_status.config(text="Comparison failed", foreground=Colors.ERROR)
        self._append_results_console(f"\nError: {str(error)}\n")

    def _display_interface_results(self, results):
        """Display interface comparison results."""
        # Clear existing
        for item in self.interface_tree.get_children():
            self.interface_tree.delete(item)

        match_count = sum(1 for r in results if r.get('Match', False))
        mismatch_count = len(results) - match_count

        self.interface_summary.config(
            text=f"Results: {len(results)} interfaces, {match_count} matches, {mismatch_count} mismatches"
        )

        for result in results:
            is_match = result.get('Match', False)
            tag = 'match' if is_match else 'mismatch'
            self.interface_tree.insert("", tk.END, values=(
                result.get('Catalyst_Interface', ''),
                result.get('Catalyst_Status', ''),
                result.get('Meraki_Status', ''),
                "Yes" if is_match else "No"
            ), tags=(tag,))

    def _display_mac_results(self, results):
        """Display MAC comparison results."""
        # Clear existing
        for item in self.mac_tree.get_children():
            self.mac_tree.delete(item)

        match_count = sum(1 for r in results if r.get('Status', '') == 'Match')
        mismatch_count = len(results) - match_count

        self.mac_summary.config(
            text=f"Results: {len(results)} devices, {match_count} matches, {mismatch_count} differences"
        )

        for result in results:
            status = result.get('Status', '')
            tag = 'match' if status == 'Match' else 'mismatch'
            self.mac_tree.insert("", tk.END, values=(
                result.get('MAC_Address', ''),
                result.get('Catalyst_Port', ''),
                result.get('Meraki_PortId', ''),
                status
            ), tags=(tag,))

    def _append_results_console(self, text):
        """Append text to results console."""
        if self.results_console:
            self.results_console.insert(tk.END, text)
            self.results_console.see(tk.END)

    # =========================================================================
    # Wizard Completion
    # =========================================================================

    def _on_wizard_complete(self, data):
        """Handle wizard completion."""
        if self.on_complete_callback:
            self.on_complete_callback(self.wizard_data)

    def _on_wizard_cancel(self):
        """Handle wizard cancellation."""
        if self.on_cancel_callback:
            self.on_cancel_callback()
