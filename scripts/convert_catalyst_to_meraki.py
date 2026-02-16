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


def valid_interface(switch_number, port_number, meraki_serials, intf_name, is_one_based):
    """
    Validates the interface based on switch number and port number.

    Args:
        switch_number (int): The switch number in the stack.
        port_number (int): The port number.
        meraki_serials (list): List of Meraki serial numbers.
        intf_name (str): Interface name for error messages.
        is_one_based (bool): True if switch numbering is 1-based (3-part format),
                             False if 0-based (2-part format).

    Returns:
        bool: True if the interface is valid, False otherwise.
    """
    if is_one_based:
        if switch_number < 1 or switch_number > len(meraki_serials):
            print(f"Switch {switch_number} does not have a corresponding Meraki serial; skipping")
            return False
    else:
        if switch_number < 0 or switch_number >= len(meraki_serials):
            print(f"Switch {switch_number} does not have a corresponding Meraki serial; skipping")
            return False

    return True


def map_interface_configs(interfaces, meraki_serials, access_group_number=0):
    """
    Maps Catalyst switch (including stacked) interface configurations to Meraki-compatible configurations.
    Auto-detects interface naming format (3-part vs 2-part) from the interface names.

    Args:
        interfaces (dict): A dictionary containing the Catalyst switch interfaces and their configurations.
        meraki_serials (list): A list of Meraki switch serial numbers, where each index corresponds to a Catalyst stack member.
        access_group_number (int): The switch stack access group number (default is 0).
                                   Only used for 3-part interfaces. I.E GigabitEthernet 1/0/1. The access group number is 0.

    Returns:
        dict: A dictionary where the keys are Meraki serial numbers, and the values are lists of Meraki-compatible port configurations.
    """
    meraki_ports_map = {serial: [] for serial in meraki_serials}

    detected = InterfaceParser.detect_format(list(interfaces.keys()))
    if detected:
        print(f"Auto-detected interface format: {detected.format_type.value} "
              f"(3-part: {detected.three_part_count}, 2-part: {detected.two_part_count})")
    else:
        print("No Ethernet interfaces detected in configuration.")

    for intf_name, catalyst_port_config in interfaces.items():
        # Auto-parse each interface individually
        parsed = InterfaceParser.parse_interface_auto(intf_name)
        if parsed is None:
            # Non-Ethernet interface (Vlan, Loopback, etc.) — skip silently
            continue

        if parsed[0] == 'three_part':
            _, switch_number, group_number, port_number = parsed

            # Validate group number
            if group_number != access_group_number:
                print(f"Port {intf_name} is not in access group {access_group_number}; skipping")
                continue

            # Validate interface (1-based indexing)
            if not valid_interface(switch_number, port_number, meraki_serials, intf_name, is_one_based=True):
                continue

            # 1-based serial lookup
            meraki_serial = meraki_serials[switch_number - 1]

        else:  # two_part
            _, switch_number, port_number = parsed

            # Validate interface (0-based indexing)
            if not valid_interface(switch_number, port_number, meraki_serials, intf_name, is_one_based=False):
                continue

            meraki_serial = meraki_serials[switch_number]

        # Build the port configuration for Meraki using the utility function
        meraki_port_config = build_meraki_port_config(port_number, catalyst_port_config)

        # Append the port config to the corresponding Meraki switch
        meraki_ports_map[meraki_serial].append(meraki_port_config)

    return meraki_ports_map


def run(meraki_api_key, meraki_cloud_ids, catalyst_ip=None,
        catalyst_config=None, access_group_number=0,
        credentials_list=None, **kwargs):
    """
    Main execution function for converting Catalyst switch configuration
    to Meraki. Interface format is auto-detected from the config.

    Args:
        meraki_api_key (str): API key for Meraki Dashboard.
        meraki_cloud_ids (list): List of Meraki serial numbers.
        catalyst_ip (str, optional): IP of the Catalyst switch.
        catalyst_config (str, optional): Pre-loaded config text.
        access_group_number (int): Access group number (default 0).
        credentials_list (list, optional): Credential dicts for Netmiko.
        **kwargs: Accepts deprecated params (e.g. device_type).

    Returns:
        None
    """
    # Step 1: Get Catalyst Config using netmiko_utils
    if not catalyst_config:
        if not catalyst_ip:
            print("Error: Either catalyst_ip or catalyst_config "
                  "must be provided.")
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
        access_group_number=access_group_number
    )

    # Count total ports mapped
    total_ports = sum(
        len(ports) for ports in meraki_ports_map.values()
    )
    print(f"Mapped {total_ports} Catalyst interfaces to Meraki "
          f"port configurations.")

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
