# Catalyst to Meraki Migration Tool

A web application for migrating Cisco Catalyst switch configurations to Cisco Meraki switches. Built with Python and Django, the tool provides a guided wizard-based workflow for configuration conversion and post-migration comparison.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Django](https://img.shields.io/badge/Django-4.2%2B-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

> **Note:** This is the **Django (web-based)** frontend. A desktop GUI version built with Tkinter is available on the [`main`](../../tree/main) branch.

## Available Frontends

| Branch | Frontend | Description |
|--------|----------|-------------|
| `main` | Tkinter | Desktop GUI (original) |
| `Django-Frontend` | Django | Web-based interface (this branch) |

Both branches share the same backend logic (models, scripts, utils). Choose the branch that matches your preferred interface.

## Features

- **Switch Migration** - Convert Catalyst running configs to Meraki port configurations via the Dashboard API
- **Interface Comparison** - Compare port status between Catalyst and Meraki after migration
- **MAC Address Comparison** - Compare MAC address tables to verify device connectivity post-migration
- **Auto-Detection** - Automatically detects interface naming formats (2-part Fa 0/1 and 3-part Gi 1/0/1) across Catalyst platforms
- **Dual Source Support** - Pull configs live from a switch via SSH or load from a saved config file
- **Multi-Stack Support** - Handles switch stacks by mapping interfaces to the correct Meraki serial number

## Architecture

The application follows Django's **MTV (Model-Template-View)** pattern, which maps to MVC:

- **Models** - Shared backend data models (credentials, serials, switch data, progress)
- **Templates** - HTML templates with Cisco-inspired CSS theme, wizard step components
- **Views** - Django views handle request logic, orchestrate network operations, and coordinate between models and templates
- Long-running operations (SSH connections, API calls) run via a background task manager to keep the web UI responsive

## Supported Platforms

The tool handles two Catalyst interface naming conventions:

| Format | Example | Platforms |
|--------|---------|-----------|
| 3-part | `GigabitEthernet1/0/1` | Catalyst 2960, 9200, 9300 |
| 2-part | `GigabitEthernet0/1` | Catalyst 3850 |

Interface format is auto-detected from the switch configuration.

## Screenshots

<!-- Add screenshots of the dashboard, conversion wizard, and comparison wizard here -->

## Prerequisites

- Python 3.8+
- Network access to target Catalyst switches (for live capture)
- A Meraki Dashboard API key with write access to the target organization

## Installation

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv venv
venv\Scripts\activate
pip install django meraki netmiko pandas
```

Set your Meraki API key using one of:

- Environment variable `MERAKI_DASHBOARD_API_KEY` or `MERAKI_API_KEY`
- Enter it in the app via **Settings**

## Usage

```bash
python manage.py migrate
python manage.py runserver
```

Then open `http://127.0.0.1:8000/` in your browser.

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
├── manage.py                              # Django management entry point
├── catalyst_meraki/                       # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│   └── migration_tool/                    # Django app
│       ├── views/                         # Django views (request handlers)
│       │   ├── dashboard.py
│       │   ├── conversion.py
│       │   ├── comparison.py
│       │   ├── settings.py
│       │   └── api.py
│       ├── templates/migration_tool/      # HTML templates
│       │   ├── base.html
│       │   ├── dashboard.html
│       │   ├── settings.html
│       │   ├── components/                # Reusable template components
│       │   ├── conversion/                # Conversion wizard steps
│       │   └── comparison/                # Comparison wizard steps
│       ├── static/migration_tool/         # CSS and JavaScript
│       │   ├── css/theme.css
│       │   └── js/console.js
│       ├── forms/                         # Django forms
│       ├── task_manager.py                # Background task execution
│       └── urls.py                        # URL routing
├── config/
│   ├── constants.py                       # Device defaults, timeouts, VLAN settings
│   └── script_types.py                    # Script type definitions
├── models/
│   ├── credentials_model.py               # In-memory credential storage
│   ├── serials_model.py                   # Meraki serial number management
│   ├── progress_model.py
│   └── switch_data_model.py               # Saved capture data (CSV + metadata)
├── scripts/
│   ├── convert_catalyst_to_meraki.py
│   ├── compare_interface_status.py
│   └── compare_mac_address_table.py
├── utils/
│   ├── interface_parser.py                # Interface name parsing & format detection
│   ├── netmiko_utils.py                   # SSH connection helpers
│   ├── port_config_builder.py             # Catalyst → Meraki config mapping
│   ├── config_manager.py                  # API key persistence
│   └── script_loader.py                   # Dynamic module loading
├── demo_configs/                          # Example Catalyst configurations
└── saved_data/                            # Saved interface/MAC captures
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

*Frontend development, documentation, and refactoring assisted by [Claude](https://claude.ai) (Anthropic).*
