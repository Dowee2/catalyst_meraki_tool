"""
Configuration package for Catalyst to Meraki migration tool.

Contains constants, device type definitions, and other configuration settings.
"""

from .constants import (
    DEFAULT_DEVICE_TYPE,
    DEFAULT_READ_TIMEOUT,
    DEFAULT_CONNECTION_TIMEOUT,
    DEFAULT_MERAKI_PORT_CONFIG,
    UPLINK_PORT_THRESHOLD,
)

from .script_types import ScriptType

__all__ = [
    'DEFAULT_DEVICE_TYPE',
    'DEFAULT_READ_TIMEOUT',
    'DEFAULT_CONNECTION_TIMEOUT',
    'DEFAULT_MERAKI_PORT_CONFIG',
    'UPLINK_PORT_THRESHOLD',
    'ScriptType',
]
