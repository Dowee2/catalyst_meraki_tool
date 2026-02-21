"""
Port Configuration Builder Utility

Builds Meraki port configurations from Catalyst switch interface configurations.
Consolidates duplicate port configuration logic from conversion scripts.
"""

import re
from typing import Dict, Any


def build_meraki_port_config(port_number: int, catalyst_port_config: str) -> Dict[str, Any]:
    """
    Build Meraki port configuration dict from Catalyst interface config.

    Parses Catalyst interface configuration text and extracts settings to create
    a corresponding Meraki port configuration dictionary.

    Args:
        port_number (int): Port number for this configuration
        catalyst_port_config (str): Raw Catalyst interface configuration text

    Returns:
        dict: Meraki port configuration dictionary with keys:
            - portId: Port number
            - name: Port description (from 'description')
            - enabled: Port status (from 'shutdown')
            - type: 'access' or 'trunk' (from 'switchport mode')
            - vlan: Access VLAN or native VLAN for trunks
            - voiceVlan: Voice VLAN (from 'switchport voice vlan')
            - allowedVlans: Allowed VLANs for trunk ports
            - poeEnabled: PoE status (from 'power inline')
            - isolationEnabled: Port isolation status
            - rstpEnabled: RSTP status (from 'spanning-tree portfast')
            - stpGuard: STP guard type (from spanning-tree bpduguard/root guard)
            - linkNegotiation: Link negotiation setting

    Example:
        >>> catalyst_config = '''
        ... interface GigabitEthernet1/0/1
        ...  description User Port
        ...  switchport access vlan 10
        ...  switchport voice vlan 20
        ...  spanning-tree portfast
        ...  spanning-tree bpduguard enable
        ... '''
        >>> config = build_meraki_port_config(1, catalyst_config)
        >>> print(config['vlan'])
        '10'
        >>> print(config['voiceVlan'])
        '20'
    """
    meraki_port_config = {
        'portId': port_number,
        'name': None,
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

    if 'shutdown' in catalyst_port_config:
        meraki_port_config['enabled'] = False

    if 'description' in catalyst_port_config:
        description_match = re.search(r'description (.+)', catalyst_port_config)
        if description_match:
            meraki_port_config['name'] = description_match.group(1).strip()

    if 'switchport mode trunk' in catalyst_port_config:
        meraki_port_config['type'] = 'trunk'

        allowed_vlans = re.search(r'switchport trunk allowed vlan (.+)', catalyst_port_config)
        if allowed_vlans:
            meraki_port_config['allowedVlans'] = allowed_vlans.group(1).strip()
        else:
            meraki_port_config['allowedVlans'] = '1-1000'

        native_vlan = re.search(r'switchport trunk native vlan (\d+)', catalyst_port_config)
        if native_vlan:
            meraki_port_config['vlan'] = native_vlan.group(1)

    else:
        access_vlan = re.search(r'switchport access vlan (\d+)', catalyst_port_config)
        if access_vlan:
            meraki_port_config['vlan'] = access_vlan.group(1)

        voice_vlan = re.search(r'switchport voice vlan (\d+)', catalyst_port_config)
        if voice_vlan:
            meraki_port_config['voiceVlan'] = voice_vlan.group(1)

    if 'spanning-tree portfast' in catalyst_port_config:
        meraki_port_config['rstpEnabled'] = True

    if 'spanning-tree bpduguard enable' in catalyst_port_config:
        meraki_port_config['stpGuard'] = 'bpdu guard'

    if 'spanning-tree guard root' in catalyst_port_config:
        meraki_port_config['stpGuard'] = 'root guard'

    if 'power inline never' in catalyst_port_config:
        meraki_port_config['poeEnabled'] = False

    return meraki_port_config
