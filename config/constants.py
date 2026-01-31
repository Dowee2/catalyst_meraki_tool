"""
Constants and Default Values

Centralizes all hardcoded values from across the codebase.
Single source of truth for device defaults, timeouts, and Meraki configurations.
"""

# =============================================================================
# Device Connection Defaults
# =============================================================================

# Default Netmiko device type for Catalyst switches
DEFAULT_DEVICE_TYPE = 'cisco_ios'

# Connection timeout in seconds
DEFAULT_CONNECTION_TIMEOUT = 60

# Read timeout for commands in seconds
DEFAULT_READ_TIMEOUT = 120

# =============================================================================
# Meraki Port Configuration Defaults
# =============================================================================

# Default port configuration for Meraki switches
# This serves as the baseline for all port configurations
DEFAULT_MERAKI_PORT_CONFIG = {
    'enabled': True,
    'type': 'access',  # 'access' or 'trunk'
    'vlan': '1',  # Default VLAN ID
    'voiceVlan': None,  # Voice VLAN ID (None if not configured)
    'allowedVlans': '1-1000',  # Allowed VLANs for trunk ports
    'poeEnabled': True,  # Power over Ethernet enabled by default
    'isolationEnabled': False,  # Port isolation
    'rstpEnabled': True,  # Rapid Spanning Tree Protocol
    'stpGuard': 'disabled',  # STP guard: 'disabled', 'bpdu guard', or 'root guard'
    'linkNegotiation': 'Auto negotiate',  # Link negotiation setting
}

# =============================================================================
# Interface and Port Thresholds
# =============================================================================

# Port number threshold for identifying uplink ports
# Ports with numbers greater than this are typically uplinks/trunk ports
# Common values: 24 (for 24-port switches), 48 (for 48-port switches)
UPLINK_PORT_THRESHOLD = 48

# =============================================================================
# Device Model Mappings
# =============================================================================

# Map of device series to their interface parser types
DEVICE_INTERFACE_PATTERNS = {
    '2960': 'catalyst_2960',  # GigabitEthernet<switch>/<group>/<port>
    '3850': 'catalyst_3850',  # GigabitEthernet<switch>/<port>
}

# =============================================================================
# Spanning Tree Protocol Settings
# =============================================================================

# STP guard types
STP_GUARD_DISABLED = 'disabled'
STP_GUARD_BPDU = 'bpdu guard'
STP_GUARD_ROOT = 'root guard'

# =============================================================================
# VLAN Settings
# =============================================================================

# Default VLAN ID
DEFAULT_VLAN = '1'

# Default allowed VLAN range for trunk ports
DEFAULT_ALLOWED_VLANS = '1-1000'

# =============================================================================
# Link Negotiation Settings
# =============================================================================

# Default link negotiation mode
DEFAULT_LINK_NEGOTIATION = 'Auto negotiate'

# Available link negotiation modes
LINK_NEGOTIATION_MODES = [
    'Auto negotiate',
    '100Megabit (auto)',
    '100 Megabit full duplex (forced)',
]
