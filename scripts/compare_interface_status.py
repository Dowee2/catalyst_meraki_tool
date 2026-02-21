import re
import os
import sys
import meraki
import pandas as pd

from utils.netmiko_utils import get_running_config
from utils.interface_parser import InterfaceParser
from config.constants import DEFAULT_READ_TIMEOUT

failures = []
credentials = []


def map_catalyst_to_meraki_interfaces(catalyst_status, meraki_serials):
    """
    Maps Catalyst interfaces to Meraki switches and ports, using the provided Meraki serial numbers.

    Args:
        catalyst_status (list): List of dictionaries representing Catalyst interface statuses.
        meraki_serials (list): List of Meraki switch serials that correspond to Catalyst stack members.

    Returns:
        dict: A dictionary where Catalyst interface names are mapped to Meraki switches and their port numbers.
    """
    mapping = {}
    for curr_interface in catalyst_status:

        interface = curr_interface['interface']
        status = curr_interface['status']

        port_number = InterfaceParser.extract_port_number(interface, 'catalyst_generic')

        if port_number is None:
            port_number = InterfaceParser.extract_port_number(interface, 'catalyst_full_interface')

        if port_number is None:
            print(f"Could not parse interface name: {interface}")
            continue

        parsed = InterfaceParser.parse_interface(interface, 'catalyst_generic')
        if parsed:
            switch_number = int(parsed[1])
        else:
            parsed = InterfaceParser.parse_interface(interface, 'catalyst_full_interface')
            if parsed:
                switch_number = int(parsed[1])
            else:
                print(f"Could not parse interface name: {interface}")
                continue

        meraki_index = switch_number - 1
        if meraki_index >= len(meraki_serials):
            print(f"No Meraki switch for Catalyst switch number {switch_number}")
            continue

        meraki_serial = meraki_serials[meraki_index]
        meraki_port_id = port_number

        mapping[interface] = {
            'meraki_serial': meraki_serial,
            'meraki_port_id': meraki_port_id,
            'catalyst_status': status,
        }

    return mapping


def get_meraki_switch_ports_statuses(api_key, meraki_serials):
    """
    Retrieves the port statuses for the specified Meraki switches using the Meraki Dashboard API.

    Args:
        api_key (str): The API key for authenticating with the Meraki Dashboard.
        meraki_serials (list): List of Meraki switch serial numbers.

    Returns:
        dict: A dictionary where Meraki serial numbers map to lists of port statuses.
    """
    dashboard = meraki.DashboardAPI(api_key, suppress_logging=True)
    meraki_ports_status = {}

    for serial in meraki_serials:
        try:
            ports_status = dashboard.switch.getDeviceSwitchPortsStatuses(serial)
            meraki_ports_status[serial] = ports_status
        except meraki.APIError as e:
            print(f"Error retrieving port statuses for Meraki switch {serial}: {e}")
            meraki_ports_status[serial] = []

    return meraki_ports_status


def compare_port_statuses(mapping, meraki_ports_status):
    """
    Compares the statuses of Catalyst interfaces and Meraki switch ports.

    Args:
        mapping (dict): A dictionary mapping Catalyst interfaces to Meraki switches and ports.
        meraki_ports_status (dict): A dictionary containing the statuses of Meraki switch ports.

    Returns:
        list: A list of dictionaries comparing the statuses of Catalyst and Meraki ports.
    """
    comparison_results = []

    for catalyst_interface, info in mapping.items():
        meraki_serial = info['meraki_serial']
        meraki_port_id = info['meraki_port_id']
        catalyst_status = info['catalyst_status']

        meraki_ports = meraki_ports_status.get(meraki_serial, [])
        meraki_status = 'unknown'
        for port in meraki_ports:
            if int(port['portId']) == meraki_port_id:
                meraki_status = port.get('status', 'unknown').lower()
                meraki_status = 'up' if meraki_status == 'connected' else 'down'
                break

        comparison_results.append({
            'Catalyst_Interface': catalyst_interface,
            'Catalyst_Status': catalyst_status,
            'Meraki_Serial': meraki_serial,
            'Meraki_PortId': meraki_port_id,
            'Meraki_Status': meraki_status,
            'Match': catalyst_status == meraki_status,
        })

    return comparison_results


def run(meraki_api_key, meraki_cloud_ids, catalyst_ip=None, catalyst_interfaces=None, name=None, credentials_list=None):
    """
    Main execution function to run the comparison between Catalyst and Meraki port statuses.

    Args:
        meraki_api_key (str): API key for accessing the Meraki Dashboard.
        meraki_cloud_ids (list): List of Meraki switch serials.
        catalyst_ip (str, optional): IP address of the Catalyst switch.
        catalyst_interfaces (list, optional): List of Catalyst interface statuses.
        name (str, optional): Hostname of the Catalyst switch.
        credentials_list (list, optional): List of credential dicts for Netmiko connection.

    Returns:
        tuple: A tuple containing comparison results and the Catalyst switch hostname.
    """
    if credentials_list is None:
        credentials_list = credentials

    if catalyst_interfaces is None:
        if not catalyst_ip:
            print("Error: Either catalyst_ip or catalyst_interfaces must be provided.")
            return None, None

        print(f"Connecting to Catalyst switch at {catalyst_ip}...")
        catalyst_interfaces, name = get_running_config(
            ip_address=catalyst_ip,
            credentials=credentials_list,
            command='show ip int brief',
            use_textfsm=True,
            read_timeout=DEFAULT_READ_TIMEOUT
        )

        if not catalyst_interfaces:
            print("Failed to retrieve Catalyst interface statuses.")
            return None, None

        print(f"Retrieved interface statuses from {name}.")
        pd.DataFrame(catalyst_interfaces).to_csv(f'{name}_interface_status.csv', index=False)

    meraki_ports_status = get_meraki_switch_ports_statuses(meraki_api_key, meraki_cloud_ids)

    mapping = map_catalyst_to_meraki_interfaces(catalyst_interfaces, meraki_cloud_ids)

    comparison_results = compare_port_statuses(mapping, meraki_ports_status)

    return comparison_results, name


if __name__ == '__main__':
    meraki_api_key = os.getenv("MERAKI_API_KEY")

    if not meraki_api_key:
        print("Error: MERAKI_API_KEY environment variable not set")
        sys.exit(1)

    print("This script should be called from the GUI or other controller.")
    print("Direct execution is not recommended.")
