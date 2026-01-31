"""
Script Type Enumeration

Defines types for different script modules in the Catalyst to Meraki tool.
Replaces string-based module selection for type safety.
"""

from enum import Enum


class ScriptType(Enum):
    """
    Enumeration of available script types.

    Used for type-safe module selection and loading.
    """

    # Conversion scripts
    CONVERT = "convert_catalyst_to_meraki"

    # Comparison scripts
    COMPARE_INTERFACES = "compare_interface_status"
    COMPARE_MAC = "compare_mac_address_table"

    def __str__(self):
        """Return the script module name."""
        return self.value

    @classmethod
    def from_device_type(cls, device_type: str) -> 'ScriptType':
        """
        Get conversion script type for a device.

        Args:
            device_type: Device type string ('2960', '3850', etc.)

        Returns:
            ScriptType.CONVERT (unified conversion script handles all device types)

        """
        # Unified conversion script handles all device types
        return cls.CONVERT

    @property
    def module_name(self) -> str:
        """Get the module name for this script type."""
        return self.value

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        display_names = {
            ScriptType.CONVERT: "Catalyst to Meraki Conversion",
            ScriptType.COMPARE_INTERFACES: "Interface Comparison",
            ScriptType.COMPARE_MAC: "MAC Address Table Comparison",
        }
        return display_names.get(self, self.value)
