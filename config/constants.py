"""
Constants and Default Values

Centralizes all hardcoded values from across the codebase.
Single source of truth for device defaults, timeouts, and Meraki configurations.
"""

DEFAULT_DEVICE_TYPE = 'cisco_ios'
DEFAULT_CONNECTION_TIMEOUT = 60
DEFAULT_READ_TIMEOUT = 120

DEFAULT_MERAKI_PORT_CONFIG = {
    'enabled': True,
    'type': 'access',
    'vlan': '1',
    'voiceVlan': None,
    'allowedVlans': '1-1000',
    'poeEnabled': True,
    'isolationEnabled': False,
    'rstpEnabled': True,
    'stpGuard': 'disabled',
    'linkNegotiation': 'Auto negotiate',
}

UPLINK_PORT_THRESHOLD = 48

STP_GUARD_DISABLED = 'disabled'
STP_GUARD_BPDU = 'bpdu guard'
STP_GUARD_ROOT = 'root guard'

DEFAULT_VLAN = '1'
DEFAULT_ALLOWED_VLANS = '1-1000'

DEFAULT_LINK_NEGOTIATION = 'Auto negotiate'

LINK_NEGOTIATION_MODES = [
    'Auto negotiate',
    '100Megabit (auto)',
    '100 Megabit full duplex (forced)',
]
