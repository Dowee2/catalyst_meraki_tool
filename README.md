# Catalyst to Meraki Migration Tool

A desktop application for migrating Cisco Catalyst switch configurations to Cisco Meraki switches. Built with Python and Tkinter, the tool provides a guided wizard-based workflow for configuration conversion and post-migration comparison.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Switch Migration** - Convert Catalyst running configs to Meraki port configurations via the Dashboard API
- **Interface Comparison** - Compare port status between Catalyst and Meraki after migration
- **MAC Address Comparison** - Compare MAC address tables to verify device connectivity post-migration
- **Auto-Detection** - Automatically detects interface naming formats (2-part and 3-part) across Catalyst platforms
- **Dual Source Support** - Pull configs live from a switch via SSH or load from a saved config file
- **Multi-Stack Support** - Handles switch stacks by mapping interfaces to the correct Meraki serial number

## Screenshots

<!-- Add screenshots of the dashboard, conversion wizard, and comparison wizard here -->

## Prerequisites

- Python 3.8+
- Network access to target Catalyst switches (for live capture)
- A Meraki Dashboard API key with write access to the target organization

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/<your-username>/catalyst-meraki-tool.git
   cd catalyst-meraki-tool
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install meraki netmiko pandas
   ```

4. Set your Meraki API key using one of:

   - Environment variable `MERAKI_DASHBOARD_API_KEY` or `MERAKI_API_KEY`
   - Enter it in the app via **Settings**

## Usage

```bash
python app.py
```

The application opens a dashboard with three options:

### Migrate Switch

A 4-step wizard that converts a Catalyst configuration to Meraki port configs:

1. **Source** - Enter the Catalyst switch IP address or select a saved config file
2. **Credentials** - Provide SSH credentials for the Catalyst switch (skipped for file source)
3. **Destination** - Enter Meraki serial number(s) for the target switch(es)
4. **Review & Execute** - Review settings and run the conversion

The tool parses the Catalyst running config, maps each interface to the corresponding Meraki switch port, and applies the configuration through the Meraki Dashboard API.

### Compare Interfaces

Capture and compare port status between the source Catalyst switch and the destination Meraki switch to verify the migration was successful.

### Compare MAC Addresses

Capture and compare MAC address tables to confirm that devices are correctly connected and communicating after migration.

## Project Structure

```
catalyst_meraki_tool/
├── app.py                     # Application entry point
├── config/
│   ├── constants.py           # Device defaults, timeouts, VLAN settings
│   ├── script_types.py        # Script type definitions
│   └── theme.py               # UI colors, fonts, and styling
├── controllers/
│   ├── app_controller.py      # Main application orchestrator
│   ├── conversion_controller.py
│   ├── comparison_controller.py
│   └── settings_controller.py
├── models/
│   ├── credentials_model.py   # In-memory credential storage
│   ├── serials_model.py       # Meraki serial number management
│   ├── progress_model.py
│   └── switch_data_model.py   # Saved capture data (CSV + metadata)
├── views/
│   ├── main_window.py         # Main application window
│   ├── dashboard_view.py      # Home screen with task cards
│   ├── settings_view.py
│   ├── components/            # Reusable UI components
│   ├── dialogs/               # Modal dialogs
│   ├── wizard/                # Base wizard framework
│   └── wizards/               # Conversion and comparison wizards
├── scripts/
│   ├── convert_catalyst_to_meraki.py
│   ├── compare_interface_status.py
│   └── compare_mac_address_table.py
├── utils/
│   ├── interface_parser.py    # Interface name parsing & format detection
│   ├── netmiko_utils.py       # SSH connection helpers
│   ├── port_config_builder.py # Catalyst → Meraki config mapping
│   ├── script_loader.py       # Dynamic module loading
│   ├── workers.py             # Background threading
│   └── console_redirect.py    # Stdout → UI redirection
└── saved_data/                # Saved interface/MAC captures
```

## Architecture

The application follows an **MVC (Model-View-Controller)** pattern:

- **Models** use an observer pattern to notify views of data changes
- **Views** are built with Tkinter and ttk, using a centralized theme inspired by Cisco branding
- **Controllers** manage business logic, orchestrate network operations, and coordinate between models and views
- Long-running operations (SSH connections, API calls) run in background threads to keep the UI responsive

## Supported Platforms

The tool handles two Catalyst interface naming conventions:

| Format | Example | Platforms |
|--------|---------|-----------|
| 3-part | `GigabitEthernet1/0/1` | Catalyst 2960, 9200, 9300 |
| 2-part | `GigabitEthernet0/1` | Catalyst 3850 |

Interface format is auto-detected from the switch configuration.

## Configuration

Default port configuration applied during conversion can be found in [config/constants.py](config/constants.py). Key defaults include:

| Setting | Default |
|---------|---------|
| Port Type | Access |
| VLAN | 1 |
| PoE | Enabled |
| RSTP | Enabled |
| STP Guard | Disabled |
| Link Negotiation | Auto negotiate |

These defaults are overridden by values parsed from the Catalyst configuration.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
