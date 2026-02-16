"""
Conversion Wizard - 4-step wizard for migrating Catalyst switch to Meraki.
"""

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from typing import Callable, Optional

from config.theme import Colors, Fonts, Spacing
from views.wizard.base_wizard import BaseWizard
from views.components.info_box import InfoBox
from views.components.ip_input import IPInput
from views.dialogs.credential_dialog import CredentialDialog, CredentialSelector
from views.dialogs.serial_dialog import SerialListManager


class ConversionWizard(ttk.Frame):
    """
    A 4-step wizard for migrating Catalyst switch configurations to Meraki.

    Steps:
    1. Source Selection - Choose IP connection or config file
    2. Credentials - Enter/select login credentials (for IP source)
    3. Destination - Enter Meraki serials and switch type
    4. Review & Execute - Summary and progress display
    """

    def __init__(
        self,
        parent,
        credentials_model,
        serials_model,
        on_complete: Optional[Callable[[dict], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Initialize the conversion wizard.

        Args:
            parent: Parent widget
            credentials_model: Model for managing credentials
            serials_model: Model for managing serial numbers
            on_complete: Callback when wizard finishes with collected data
            on_cancel: Callback when wizard is cancelled
        """
        super().__init__(parent, **kwargs)
        self.credentials_model = credentials_model
        self.serials_model = serials_model
        self.on_complete_callback = on_complete
        self.on_cancel_callback = on_cancel

        # Wizard data storage
        self.wizard_data = {
            'source_type': 'ip',  # 'ip' or 'file'
            'catalyst_ip': '',
            'config_file_path': '',
            'hostname': '',
            'credentials': None,
            'meraki_serials': [],
        }

        # UI references
        self.source_var = None
        self.ip_input = None
        self.file_path_entry = None
        self.hostname_entry = None
        self.cred_display_label = None
        self.serials_display = None
        self.console = None

        self._create_wizard()

    def _create_wizard(self):
        """Create the wizard with all steps."""
        steps = [
            {
                'name': 'Source',
                'title': 'Step 1 of 4: Get Old Switch information.',
                'description': 'Choose how to get the switch configuration',
                'create_content': self._create_source_step,
                'validate': self._validate_source_step,
                'on_leave': self._save_source_data
            },
            {
                'name': 'Login',
                'title': 'Step 2 of 4: Login credentials',
                'description': 'Enter the credentials to connect to your switch',
                'create_content': self._create_credentials_step,
                'validate': self._validate_credentials_step,
                'on_enter': self._on_credentials_enter,
                'on_leave': self._save_credentials_data
            },
            {
                'name': 'Destination',
                'title': 'Step 3 of 4: Your new Meraki switch',
                'description': 'Enter the details for your new Meraki switch',
                'create_content': self._create_destination_step,
                'validate': self._validate_destination_step,
                'on_leave': self._save_destination_data
            },
            {
                'name': 'Migrate',
                'title': 'Step 4 of 4: Ready to migrate',
                'description': 'Review your settings and start the migration',
                'create_content': self._create_review_step,
                'on_enter': self._update_review_summary
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
    # Step 1: Source Selection
    # =========================================================================

    def _create_source_step(self, content_frame):
        """Create the source selection step UI."""
        self.source_var = tk.StringVar(value='ip')

        self._create_source_info_box(content_frame)
        self._create_source_radio_buttons(content_frame)
        self._create_ip_source_content(content_frame)
        self._create_file_source_content(content_frame)

        # Initially hide file container
        self.file_container.pack_forget()

    def _create_source_info_box(self, parent):
        """Create the help info box for source selection."""
        info_frame = ttk.Frame(parent, style="Card.TFrame")
        info_frame.pack(fill=tk.X, pady=(Spacing.LG, 0))

        InfoBox(
            info_frame,
            title="Not sure which to choose?",
            message="If you can access the switch from this computer, use 'Connect over network'. "
                    "Otherwise, export the running config from the switch and use 'Configuration file'.",
            box_type='help'
        ).pack(fill=tk.X)

    def _create_source_radio_buttons(self, parent):
        """Create the source type radio buttons side by side."""
        radio_frame = ttk.Frame(parent, style="Card.TFrame")
        radio_frame.pack(fill=tk.X, pady=Spacing.SM)

        ttk.Radiobutton(
            radio_frame,
            text="Connect to switch over the network",
            variable=self.source_var,
            value='ip',
            command=self._on_source_changed,
            style="Card.TRadiobutton"
        ).pack(side=tk.LEFT, padx=(0, Spacing.LG))

        ttk.Radiobutton(
            radio_frame,
            text="I have a configuration file",
            variable=self.source_var,
            value='file',
            command=self._on_source_changed,
            style="Card.TRadiobutton"
        ).pack(side=tk.LEFT)

    def _create_ip_source_content(self, parent):
        """Create the IP input content area."""
        self.ip_container = ttk.Frame(parent, style="Card.TFrame")
        self.ip_container.pack(fill=tk.X, padx=(Spacing.XL, 0), pady=Spacing.SM)

        self.ip_input = IPInput(
            self.ip_container,
            label="Old switch address:",
            placeholder="192.168.1.1"
        )
        self.ip_input.pack(fill=tk.X)

    def _create_file_source_content(self, parent):
        """Create the file input content area."""
        self.file_container = ttk.Frame(parent, style="Card.TFrame")
        self.file_container.pack(fill=tk.X, padx=(Spacing.XL, 0), pady=Spacing.SM)

        self._create_file_path_input()
        self._create_hostname_input()

    def _create_file_path_input(self):
        """Create the file path input with browse button."""
        file_path_frame = ttk.Frame(self.file_container, style="Card.TFrame")
        file_path_frame.pack(fill=tk.X)

        ttk.Label(
            file_path_frame,
            text="Configuration file:",
            style="Card.TLabel"
        ).pack(anchor=tk.W)

        file_entry_frame = ttk.Frame(file_path_frame, style="Card.TFrame")
        file_entry_frame.pack(fill=tk.X, pady=(Spacing.XS, 0))

        self.file_path_entry = ttk.Entry(file_entry_frame, width=40)
        self.file_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            file_entry_frame,
            text="Browse...",
            style="Secondary.TButton",
            command=self._browse_config_file
        ).pack(side=tk.LEFT, padx=(Spacing.SM, 0))

    def _create_hostname_input(self):
        """Create the hostname input field."""
        hostname_frame = ttk.Frame(self.file_container, style="Card.TFrame")
        hostname_frame.pack(fill=tk.X, pady=(Spacing.MD, 0))

        ttk.Label(
            hostname_frame,
            text="Switch name (hostname):",
            style="Card.TLabel"
        ).pack(anchor=tk.W)

        self.hostname_entry = ttk.Entry(hostname_frame, width=30)
        self.hostname_entry.pack(anchor=tk.W, pady=(Spacing.XS, 0))


    def _on_source_changed(self):
        """Handle source type radio button change."""
        source = self.source_var.get()
        if source == 'ip':
            self.file_container.pack_forget()
            self.ip_container.pack(fill=tk.X, padx=(Spacing.XL, 0), pady=Spacing.SM)
        else:
            self.ip_container.pack_forget()
            self.file_container.pack(fill=tk.X, padx=(Spacing.XL, 0), pady=Spacing.SM)

    def _browse_config_file(self):
        """Open file dialog to select config file."""
        file_path = filedialog.askopenfilename(
            title="Select Configuration File",
            filetypes=[("Text files", "*.txt"), ("Config files", "*.cfg"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)

    def _validate_source_step(self):
        """Validate the source step."""
        source = self.source_var.get()

        if source == 'ip':
            is_valid, error = self.ip_input.validate()
            return is_valid, error
        else:
            # File source
            file_path = self.file_path_entry.get().strip()
            hostname = self.hostname_entry.get().strip()

            if not file_path:
                return False, "Please select a configuration file"
            if not os.path.exists(file_path):
                return False, "The selected file does not exist"
            if not hostname:
                return False, "Please enter the switch hostname"

            return True, ""

    def _save_source_data(self):
        """Save source step data to wizard_data."""
        self.wizard_data['source_type'] = self.source_var.get()

        if self.wizard_data['source_type'] == 'ip':
            self.wizard_data['catalyst_ip'] = self.ip_input.get_value()
        else:
            self.wizard_data['config_file_path'] = self.file_path_entry.get().strip()
            self.wizard_data['hostname'] = self.hostname_entry.get().strip()

    # =========================================================================
    # Step 2: Credentials
    # =========================================================================

    def _create_credentials_step(self, content_frame):
        """Create the credentials step UI."""
        self._create_saved_credentials_section(content_frame)
        self._create_new_credentials_section(content_frame)
        self._create_selected_credential_indicator(content_frame)

    def _create_saved_credentials_section(self, parent):
        """Create the saved credentials selection section."""
        saved_frame = ttk.LabelFrame(
            parent,
            text="Saved login details",
            style="Card.TLabelframe"
        )
        saved_frame.pack(fill=tk.X, pady=Spacing.SM)

        self.cred_list_frame = ttk.Frame(saved_frame)
        self.cred_list_frame.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD)

        self.cred_display_label = ttk.Label(
            self.cred_list_frame,
            text="No saved credentials",
            style="Secondary.TLabel"
        )
        self.cred_display_label.pack(anchor=tk.W)

        self._create_credentials_listbox()
        self._create_saved_credentials_buttons(saved_frame)

    def _create_credentials_listbox(self):
        """Create the credentials selection listbox."""
        self.cred_listbox = tk.Listbox(
            self.cred_list_frame,
            height=4,
            font=Fonts.NORMAL,
            bg=Colors.BG_CARD,
            fg=Colors.TEXT_PRIMARY,
            selectbackground=Colors.PRIMARY,
            selectforeground=Colors.TEXT_BUTTON
        )
        self.cred_listbox.pack(fill=tk.X, pady=(Spacing.SM, 0))
        self.cred_listbox.pack_forget()  # Hidden initially

    def _create_saved_credentials_buttons(self, parent):
        """Create buttons for saved credentials management."""
        saved_btn_frame = ttk.Frame(parent)
        saved_btn_frame.pack(fill=tk.X, padx=Spacing.MD, pady=(0, Spacing.MD))

        self.use_saved_btn = ttk.Button(
            saved_btn_frame,
            text="Use Selected",
            style="Primary.TButton",
            command=self._use_selected_credential
        )
        self.use_saved_btn.pack(side=tk.LEFT, padx=(0, Spacing.SM))
        self.use_saved_btn.pack_forget()

        ttk.Button(
            saved_btn_frame,
            text="Manage Saved Credentials",
            style="Secondary.TButton",
            command=self._manage_credentials
        ).pack(side=tk.LEFT)

    def _create_new_credentials_section(self, parent):
        """Create the new credentials entry section."""
        new_frame = ttk.LabelFrame(
            parent,
            text="Or enter new credentials",
            style="Card.TLabelframe"
        )
        new_frame.pack(fill=tk.X, pady=Spacing.MD)

        new_inner = ttk.Frame(new_frame)
        new_inner.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD)

        # Username
        ttk.Label(new_inner, text="Username:").grid(
            row=0, column=0, padx=Spacing.SM, pady=Spacing.SM, sticky=tk.W)
        self.new_username = ttk.Entry(new_inner, width=30)
        self.new_username.grid(row=0, column=1, padx=Spacing.SM, pady=Spacing.SM, sticky=tk.W)

        # Password
        ttk.Label(new_inner, text="Password:").grid(
            row=1, column=0, padx=Spacing.SM, pady=Spacing.SM, sticky=tk.W)
        self.new_password = ttk.Entry(new_inner, width=30, show="*")
        self.new_password.grid(row=1, column=1, padx=Spacing.SM, pady=Spacing.SM, sticky=tk.W)

        # Use new button
        ttk.Button(
            new_inner,
            text="Use These Credentials",
            style="Primary.TButton",
            command=self._use_new_credentials
        ).grid(row=2, column=0, columnspan=2, pady=Spacing.MD)

    def _create_selected_credential_indicator(self, parent):
        """Create the selected credential status indicator."""
        self.selected_cred_frame = ttk.Frame(parent, style="Card.TFrame")
        self.selected_cred_frame.pack(fill=tk.X, pady=Spacing.MD)

        self.selected_cred_label = ttk.Label(
            self.selected_cred_frame,
            text="",
            style="Card.TLabel",
            font=Fonts.BOLD
        )
        self.selected_cred_label.pack(anchor=tk.W)

    def _on_credentials_enter(self):
        """Called when entering the credentials step."""
        # Skip this step if source is file
        if self.wizard_data['source_type'] == 'file':
            self.wizard._on_next()
            return

        # Refresh credentials list
        self._refresh_credentials_list()

    def _refresh_credentials_list(self):
        """Refresh the credentials listbox."""
        creds = self.credentials_model.get_credentials()
        self.cred_listbox.delete(0, tk.END)

        if creds:
            self.cred_display_label.pack_forget()
            self.cred_listbox.pack(fill=tk.X, pady=(Spacing.SM, 0))
            self.use_saved_btn.pack(side=tk.LEFT, padx=(0, Spacing.SM))

            for cred in creds:
                display = f"{cred.get('description', 'No description')} ({cred.get('username', '')})"
                self.cred_listbox.insert(tk.END, display)

            # Select first item
            self.cred_listbox.selection_set(0)
        else:
            self.cred_listbox.pack_forget()
            self.use_saved_btn.pack_forget()
            self.cred_display_label.config(text="No saved credentials")
            self.cred_display_label.pack(anchor=tk.W)

    def _use_selected_credential(self):
        """Use the selected saved credential."""
        selected = self.cred_listbox.curselection()
        if selected:
            index = selected[0]
            creds = self.credentials_model.get_credentials()
            if 0 <= index < len(creds):
                self.wizard_data['credentials'] = creds[index]
                self._update_selected_credential_display()

    def _use_new_credentials(self):
        """Use newly entered credentials."""
        username = self.new_username.get().strip()
        password = self.new_password.get()

        if not username or not password:
            self.wizard.show_error("Please enter both username and password")
            return

        self.wizard_data['credentials'] = {
            'username': username,
            'password': password,
            'description': f'{username} (entered manually)'
        }
        self._update_selected_credential_display()
        self.wizard.clear_error()

    def _update_selected_credential_display(self):
        """Update the display showing which credential is selected."""
        if self.wizard_data['credentials']:
            cred = self.wizard_data['credentials']
            self.selected_cred_label.config(
                text=f"Selected: {cred.get('username', '')}",
                foreground=Colors.SUCCESS
            )

    def _manage_credentials(self):
        """Open the credential management dialog."""
        from views.dialogs.credential_dialog import CredentialListManager

        dialog = CredentialListManager(self, self.credentials_model.get_credentials())
        self.wait_window(dialog)

        if dialog.result is not None:
            self.credentials_model.clear_credentials()
            for cred in dialog.result:
                self.credentials_model.add_credential(cred)
            self._refresh_credentials_list()

    def _validate_credentials_step(self):
        """Validate the credentials step."""
        # Skip validation if source is file
        if self.wizard_data['source_type'] == 'file':
            return True, ""

        if not self.wizard_data['credentials']:
            return False, "Please select or enter credentials"
        return True, ""

    def _save_credentials_data(self):
        """Save credentials data."""
        # Already saved when selecting/entering credentials
        pass

    # =========================================================================
    # Step 3: Destination
    # =========================================================================

    def _create_destination_step(self, content_frame):
        """Create the destination step UI."""
        self._create_serials_section(content_frame)
        self._update_serials_display()

    def _create_serials_section(self, parent):
        """Create the Meraki serial numbers section."""
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
                    "For switch stacks, enter them in the correct order.",
            box_type='info'
        ).pack(fill=tk.X, padx=Spacing.MD, pady=(0, Spacing.MD))

    def _manage_serials(self):
        """Open the serial management dialog."""
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

    def _validate_destination_step(self):
        """Validate the destination step."""
        if not self.wizard_data['meraki_serials']:
            return False, "Please add at least one Meraki serial number"
        return True, ""

    def _save_destination_data(self):
        """Save destination data."""
        pass

    # =========================================================================
    # Step 4: Review & Execute
    # =========================================================================

    def _create_review_step(self, content_frame):
        """Create the review and execute step UI."""
        # Summary section
        summary_frame = ttk.LabelFrame(
            content_frame,
            text="Migration Summary",
            style="Card.TLabelframe"
        )
        summary_frame.pack(fill=tk.X, pady=Spacing.SM)

        self.summary_text = tk.Text(
            summary_frame,
            height=8,
            font=Fonts.NORMAL,
            bg=Colors.BG_CARD,
            fg=Colors.TEXT_PRIMARY,
            state='disabled',
            wrap=tk.WORD
        )
        self.summary_text.pack(fill=tk.X, padx=Spacing.MD, pady=Spacing.MD)

        # Progress/console section
        console_frame = ttk.LabelFrame(
            content_frame,
            text="Progress",
            style="Card.TLabelframe"
        )
        console_frame.pack(fill=tk.BOTH, expand=True, pady=Spacing.MD)

        self.console = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            font=Fonts.SMALL,
            bg=Colors.BG_CARD,
            fg=Colors.TEXT_PRIMARY,
            height=10
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=Spacing.MD, pady=Spacing.MD)

    def _update_review_summary(self):
        """Update the review summary with collected data."""
        data = self.wizard_data

        # Build summary text
        lines = []

        if data['source_type'] == 'ip':
            lines.append(f"Source: Connect to switch at {data['catalyst_ip']}")
            if data['credentials']:
                lines.append(f"Login as: {data['credentials'].get('username', 'N/A')}")
        else:
            lines.append(f"Source: Configuration file")
            lines.append(f"  File: {data['config_file_path']}")
            lines.append(f"  Hostname: {data['hostname']}")

        lines.append("")
        lines.append("Interface format: Auto-detected from configuration")
        lines.append("")
        lines.append(f"Meraki serial numbers ({len(data['meraki_serials'])}):")
        for i, serial in enumerate(data['meraki_serials'], 1):
            lines.append(f"  {i}. {serial}")

        # Update text widget
        self.summary_text.config(state='normal')
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', '\n'.join(lines))
        self.summary_text.config(state='disabled')

        # Clear console
        self.console.delete('1.0', tk.END)

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

    # =========================================================================
    # Public Methods
    # =========================================================================

    def get_console(self):
        """Get the console widget for output."""
        return self.console

    def append_console(self, text):
        """Append text to the console."""
        if self.console:
            self.console.insert(tk.END, text)
            self.console.see(tk.END)

    def clear_console(self):
        """Clear the console."""
        if self.console:
            self.console.delete('1.0', tk.END)

    def get_wizard_data(self):
        """Get the collected wizard data."""
        return self.wizard_data.copy()
