"""
Local configuration manager for the Catalyst to Meraki Migration Tool.
Stores user settings in a JSON file under the user's home directory,
avoiding any dependency on OS-level environment variables.
"""

import os
import json

_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".catalyst_meraki_tool")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "config.json")


def _load() -> dict:
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save(data: dict) -> None:
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    with open(_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_api_key() -> str:
    return _load().get("meraki_api_key", "")


def save_api_key(api_key: str) -> None:
    data = _load()
    data["meraki_api_key"] = api_key
    _save(data)
