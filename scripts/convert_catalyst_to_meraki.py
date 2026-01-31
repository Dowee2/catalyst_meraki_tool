import re
import sys
import os
import meraki

# Use relative imports for all internal modules
from utils.netmiko_utils import get_running_config
from utils.port_config_builder import build_meraki_port_config
from utils.interface_parser import InterfaceParser
from config.constants import DEFAULT_READ_TIMEOUT

# Suppress warnings related to SSL certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def parse_interfaces(config):
    """
    Parses the interface configurations from the Catalyst switch's running config.

    Args:
        config (str): The running configuration from the Catalyst switch.

    Returns:
        dict: A dictionary where the keys are interface names and values are configurations.
    """
    interfaces = {}
    interface_sections = re.findall(r'interface (\S+)(.*?)!', config, re.DOTALL)
    for intf, cfg in interface_sections:
        interfaces[intf] = cfg
    return interfaces


def configure_meraki_switch_ports(api_key, meraki_ports_map):
    """
    Configures Meraki switch ports (stacked switches included) using the Meraki Dashboard API.

    Args:
        api_key (str): API key for authenticating with the Meraki Dashboard.
        meraki_ports_map (dict): A dictionary where keys are Meraki serial numbers and values are lists of port configurations.
    """
    dashboard = meraki.DashboardAPI(api_key)

    # Iterate through each Meraki switch serial and update its corresponding ports
    for serial, ports in meraki_ports_map.items():
        try:
            # Retrieve the existing ports on the Meraki switch
            existing_ports = dashboard.switch.getDeviceSwitchPorts(serial)
            existing_port_ids = [str(port['portId']) for port in existing_ports]
        except meraki.APIError as e:
            print(f"Error retrieving existing ports for switch {serial}: {e}")
            sys.exit(1)

        # Update switch ports with new configurations
        for port in ports:
            if str(port['portId']) not in existing_port_ids:
                print(f"Port {port['portId']} does not exist on the Meraki switch {serial}.")
                continue
            try:
                dashboard.switch.updateDeviceSwitchPort(
                    serial,
                    portId=port['portId'],
                    name=port['name'],
                    tags=None,
                    enabled=port['enabled'],
                    type=port['type'],
                    vlan=int(port['vlan']),
                    voiceVlan=int(port['voiceVlan']) if port['voiceVlan'] else None,
                    allowedVlans=port['allowedVlans'] if port['type'] == 'trunk' else '1-1000',
                    poeEnabled=port['poeEnabled'],
                    isolationEnabled=port['isolationEnabled'],
                    rstpEnabled=port['rstpEnabled'],
                    stpGuard=port['stpGuard'],
                    linkNegotiation=port['linkNegotiation']
                )
                print(f"Updated port {port['portId']} on Meraki switch {serial}")
            except meraki.APIError as e:
                print(f"Error updating port {port['portId']} on Meraki switch {serial}: {e}")


def valid_interface(switch_number, port_number, meraki_serials, intf_name, device_type, access_group_number=0):
    """
    Validates the interface based on switch number and port number.

    Args:
        switch_number (int): The switch number in the stack.
        port_number (int): The port number.
        meraki_serials (list): List of Meraki serial numbers.
        intf_name (str): Interface name for error messages.
        device_type (str): Device type ('catalyst_2960' or 'catalyst_3850').
        access_group_number (int): The switch stack access group number (only for 2960).

    Returns:
        bool: True if the interface is valid, False otherwise.
    """
    # Check if switch number is within bounds
    # For 2960: switch_number is 1-based
    # For 3850: switch_number is 0-based
    if device_type == 'catalyst_2960':
        # 2960 uses 1-based indexing: switch 1, 2, 3...
        if switch_number < 1 or switch_number > len(meraki_serials):
            print(f"Switch {switch_number} does not have a corresponding Meraki serial; skipping")
            return False
    else:
        # 3850 uses 0-based indexing: switch 0, 1, 2...
        if switch_number < 0 or switch_number >= len(meraki_serials):
            print(f"Switch {switch_number} does not have a corresponding Meraki serial; skipping")
            return False

    return True


def map_interface_configs(interfaces, meraki_serials, device_type='catalyst_2960', access_group_number=0):
    """
    Maps Catalyst switch (including stacked) interface configurations to Meraki-compatible configurations.
    This function takes into account that each stack switch corresponds to a Meraki switch based on the list of serials provided.

    Args:
        interfaces (dict): A dictionary containing the Catalyst switch interfaces and their configurations.
        meraki_serials (list): A list of Meraki switch serial numbers, where each index corresponds to a Catalyst stack member.
        device_type (str): Device type ('catalyst_2960' or 'catalyst_3850'). Default: 'catalyst_2960'
        access_group_number (int): The switch stack access group number (default is 0).
                                   Only used for 2960. I.E GigabitEthernet 1/0/1. The access group number is 0.

    Returns:
        dict: A dictionary where the keys are Meraki serial numbers, and the values are lists of Meraki-compatible port configurations.
    """
    meraki_ports_map = {serial: [] for serial in meraki_serials}

    for intf_name, catalyst_port_config in interfaces.items():
        # Skip non-Ethernet interfaces
        if not intf_name.startswith('GigabitEthernet'):
            continue

        # Parse interface using InterfaceParser
        parsed = InterfaceParser.parse_interface(intf_name, device_type)
        if not parsed:
            print(f"Could not parse interface {intf_name} for device type {device_type}")
            continue

        # Extract components based on device type
        if device_type == 'catalyst_2960':
            # 2960: GigabitEthernet<switch>/<group>/<port>
            # Returns: (switch_number, group_number, port_number)
            try:
                switch_number, group_number, port_number = [int(x) for x in parsed]
            except (ValueError, TypeError):
                print(f"Invalid interface numbering in {intf_name}")
                continue

            # Validate group number for 2960
            if group_number != access_group_number:
                print(f"Port {intf_name} is not in access group {access_group_number}; skipping")
                continue

            # Validate interface
            if not valid_interface(switch_number, port_number, meraki_serials, intf_name, device_type, access_group_number):
                continue

            # Get the corresponding Meraki serial (2960 uses 1-based indexing)
            meraki_serial = meraki_serials[switch_number - 1]

        else:  # catalyst_3850
            # 3850: GigabitEthernet<switch>/<port>
            # Returns: (switch_number, port_number)
            try:
                switch_number, port_number = [int(x) for x in parsed]
            except (ValueError, TypeError):
                print(f"Invalid interface numbering in {intf_name}")
                continue

            # Validate interface
            if not valid_interface(switch_number, port_number, meraki_serials, intf_name, device_type):
                continue

            # Get the corresponding Meraki serial (3850 uses 0-based indexing)
            meraki_serial = meraki_serials[switch_number]

        # Build the port configuration for Meraki using the utility function
        meraki_port_config = build_meraki_port_config(port_number, catalyst_port_config)

        # Append the port config to the corresponding Meraki switch
        meraki_ports_map[meraki_serial].append(meraki_port_config)

    return meraki_ports_map


def run(meraki_api_key, meraki_cloud_ids, catalyst_ip=None, catalyst_config=None,
        device_type='catalyst_2960', access_group_number=0, credentials_list=None):
    """
    Main execution function for converting Catalyst switch configuration to Meraki.

    Args:
        meraki_api_key (str): API key for authenticating with the Meraki Dashboard.
        meraki_cloud_ids (list): List of Meraki switch serial numbers corresponding to stack members.
        catalyst_ip (str, optional): IP address of the Catalyst switch (if retrieving config remotely).
        catalyst_config (str, optional): Pre-loaded Catalyst configuration text (skips remote retrieval).
        device_type (str): Device type - 'catalyst_2960' or 'catalyst_3850'. Default: 'catalyst_2960'
        access_group_number (int): Switch stack access group number for 2960 (default is 0).
        credentials_list (list, optional): List of credential dicts for Netmiko connection.

    Returns:
        None
    """
    # Step 1: Get Catalyst Config using netmiko_utils
    if not catalyst_config:
        if not catalyst_ip:
            print("Error: Either catalyst_ip or catalyst_config must be provided.")
            sys.exit(1)

        print(f"Connecting to Catalyst switch at {catalyst_ip}...")
        catalyst_config, hostname = get_running_config(
            ip_address=catalyst_ip,
            credentials=credentials_list,
            command='show running-config',
            use_textfsm=False,
            read_timeout=DEFAULT_READ_TIMEOUT
        )

        if not catalyst_config:
            print("Failed to retrieve Catalyst configuration.")
            sys.exit(1)
        print(f"Catalyst configuration retrieved from {hostname}.")

    # Step 2: Parse Interfaces
    interfaces = parse_interfaces(catalyst_config)
    print(f"Parsed {len(interfaces)} interfaces from configuration.")

    # Step 3: Map Interface Configs to Meraki Format
    meraki_ports_map = map_interface_configs(
        interfaces,
        meraki_cloud_ids,
        device_type=device_type,
        access_group_number=access_group_number
    )

    # Count total ports mapped
    total_ports = sum(len(ports) for ports in meraki_ports_map.values())
    print(f"Mapped {total_ports} Catalyst interfaces to Meraki port configurations for {device_type}.")

    # Step 4: Configure Meraki Switch Ports
    configure_meraki_switch_ports(meraki_api_key, meraki_ports_map)
    print("Port configurations applied to Meraki switches.")


if __name__ == "__main__":
    # Example usage - DO NOT use hardcoded IPs in production
    # This is for testing only

    # Example for 2960
    # catalyst_ip = "10.x.x.x"
    # device_type = "catalyst_2960"
    # meraki_serials = ["SERIAL1", "SERIAL2"]

    # Example for 3850
    # catalyst_ip = "10.x.x.x"
    # device_type = "catalyst_3850"
    # meraki_serials = ["SERIAL1", "SERIAL2"]

    meraki_api_key = os.getenv("MERAKI_API_KEY")

    if not meraki_api_key:
        print("Error: MERAKI_API_KEY environment variable not set")
        sys.exit(1)

    print("This script should be called from the GUI or other controller.")
    print("Direct execution is not recommended.")
