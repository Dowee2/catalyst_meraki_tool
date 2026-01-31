"""
Interface Parser Utility

Centralizes interface name parsing patterns for different Catalyst switch models.
Consolidates regex patterns scattered across multiple script files.
"""

import re
from typing import Optional, Tuple, Dict


class InterfaceParser:
    """
    Parser for Catalyst switch interface names.

    Provides regex patterns and parsing methods for different switch models.
    Supports varying interface naming conventions (GigabitEthernet, FastEthernet, etc.)
    and port numbering schemes.
    """

    # Interface patterns for different device types
    PATTERNS = {
        # Catalyst 2960: GigabitEthernet<switch>/<group>/<port>
        # Example: GigabitEthernet1/0/1
        'catalyst_2960': r'GigabitEthernet(\d+)/(\d+)/(\d+)',

        # Catalyst 3850: GigabitEthernet<switch>/<port>
        # Example: GigabitEthernet1/1
        'catalyst_3850': r'GigabitEthernet(\d+)/(\d+)',

        # Generic pattern for comparison scripts: (Gi|Fa)<switch>/.../<port>
        # Matches both GigabitEthernet and FastEthernet abbreviated
        # Example: Gi1/0/1 or Fa2/0/24
        'catalyst_generic': r'(Gi|Fa)(\d+)/\d+/(\d+)',

        # Full interface names for comparison
        # Example: GigabitEthernet1/0/1 or FastEthernet2/0/24
        'catalyst_full_interface': r'(GigabitEthernet|FastEthernet)(\d+)/\d+/(\d+)',
    }

    @classmethod
    def parse_interface(cls, interface_name: str, device_type: str = 'catalyst_2960') -> Optional[Tuple]:
        """
        Parse interface name into its components.

        Args:
            interface_name (str): Full interface name (e.g., 'GigabitEthernet1/0/1')
            device_type (str): Device type key from PATTERNS dict.
                              Options: 'catalyst_2960', 'catalyst_3850', 'catalyst_generic'
                              Default: 'catalyst_2960'

        Returns:
            tuple: Parsed interface components, or None if parsing fails
                  - For 2960: (switch_number, group_number, port_number)
                  - For 3850: (switch_number, port_number)
                  - For generic: (interface_type, switch_number, port_number)

        Example:
            >>> InterfaceParser.parse_interface('GigabitEthernet1/0/24', 'catalyst_2960')
            ('1', '0', '24')

            >>> InterfaceParser.parse_interface('GigabitEthernet2/10', 'catalyst_3850')
            ('2', '10')

            >>> InterfaceParser.parse_interface('Gi1/0/1', 'catalyst_generic')
            ('Gi', '1', '1')
        """
        if device_type not in cls.PATTERNS:
            raise ValueError(f"Unknown device type: {device_type}. "
                           f"Valid types: {list(cls.PATTERNS.keys())}")

        pattern = cls.PATTERNS[device_type]
        match = re.match(pattern, interface_name)

        if match:
            return match.groups()
        return None

    @classmethod
    def is_valid_interface(cls, interface_name: str, device_type: str = 'catalyst_2960') -> bool:
        """
        Check if interface name matches expected pattern for device type.

        Args:
            interface_name (str): Interface name to validate
            device_type (str): Device type key from PATTERNS dict. Default: 'catalyst_2960'

        Returns:
            bool: True if interface name matches pattern, False otherwise

        Example:
            >>> InterfaceParser.is_valid_interface('GigabitEthernet1/0/1', 'catalyst_2960')
            True

            >>> InterfaceParser.is_valid_interface('GigabitEthernet1/0/1', 'catalyst_3850')
            False

            >>> InterfaceParser.is_valid_interface('FastEthernet1/0/1', 'catalyst_2960')
            False
        """
        return cls.parse_interface(interface_name, device_type) is not None

    @classmethod
    def extract_port_number(cls, interface_name: str, device_type: str = 'catalyst_2960') -> Optional[int]:
        """
        Extract just the port number from an interface name.

        Args:
            interface_name (str): Full interface name
            device_type (str): Device type key. Default: 'catalyst_2960'

        Returns:
            int: Port number, or None if parsing fails

        Example:
            >>> InterfaceParser.extract_port_number('GigabitEthernet1/0/24', 'catalyst_2960')
            24

            >>> InterfaceParser.extract_port_number('GigabitEthernet2/10', 'catalyst_3850')
            10
        """
        parsed = cls.parse_interface(interface_name, device_type)
        if not parsed:
            return None

        # Port number is always the last component
        try:
            return int(parsed[-1])
        except (ValueError, IndexError):
            return None

    @classmethod
    def get_interface_prefix(cls, interface_name: str) -> Optional[str]:
        """
        Extract interface type prefix (GigabitEthernet, FastEthernet, etc.).

        Args:
            interface_name (str): Full interface name

        Returns:
            str: Interface type prefix, or None if not found

        Example:
            >>> InterfaceParser.get_interface_prefix('GigabitEthernet1/0/1')
            'GigabitEthernet'

            >>> InterfaceParser.get_interface_prefix('Gi1/0/1')
            'Gi'

            >>> InterfaceParser.get_interface_prefix('FastEthernet2/0/24')
            'FastEthernet'
        """
        # Try to match common interface prefixes
        prefixes = ['GigabitEthernet', 'FastEthernet', 'TenGigabitEthernet', 'Gi', 'Fa', 'Te']
        for prefix in prefixes:
            if interface_name.startswith(prefix):
                return prefix
        return None

    @classmethod
    def filter_interfaces(cls, interface_names: list, device_type: str = 'catalyst_2960',
                         include_prefixes: Optional[list] = None) -> list:
        """
        Filter list of interface names to only valid interfaces for device type.

        Args:
            interface_names (list): List of interface names to filter
            device_type (str): Device type key. Default: 'catalyst_2960'
            include_prefixes (list, optional): Only include interfaces with these prefixes.
                                              Example: ['GigabitEthernet'] to exclude FastEthernet

        Returns:
            list: Filtered list of valid interface names

        Example:
            >>> interfaces = ['GigabitEthernet1/0/1', 'Vlan1', 'GigabitEthernet1/0/2']
            >>> InterfaceParser.filter_interfaces(interfaces, 'catalyst_2960')
            ['GigabitEthernet1/0/1', 'GigabitEthernet1/0/2']

            >>> InterfaceParser.filter_interfaces(interfaces, 'catalyst_2960',
            ...                                   include_prefixes=['GigabitEthernet'])
            ['GigabitEthernet1/0/1', 'GigabitEthernet1/0/2']
        """
        filtered = []
        for interface in interface_names:
            # Check if valid for device type
            if not cls.is_valid_interface(interface, device_type):
                continue

            # Check prefix filter if specified
            if include_prefixes:
                prefix = cls.get_interface_prefix(interface)
                if prefix not in include_prefixes:
                    continue

            filtered.append(interface)

        return filtered
