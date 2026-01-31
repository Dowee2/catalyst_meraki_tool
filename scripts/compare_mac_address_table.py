import re
import os
import sys
import meraki
import pandas as pd
from datetime import datetime, timedelta

# Use relative imports for all internal modules
from utils.netmiko_utils import get_running_config
from utils.interface_parser import InterfaceParser
from config.constants import UPLINK_PORT_THRESHOLD

# List to store failed connection attempts (kept for compatibility)
failures = []

# Global credentials list (kept for compatibility with controller)
credentials = []

# Function to get clients from Meraki switches
def get_meraki_clients(api_key, meraki_serials):
    dashboard = meraki.DashboardAPI(api_key, suppress_logging=True)
    meraki_clients = {}
    for serial in meraki_serials:
        try:
            # Retrieve clients connected to the device in the last day (86400 seconds)
            timespan = 86400  # 1 day
            clients = dashboard.devices.getDeviceClients(serial, timespan=timespan)
            meraki_clients[serial] = clients
        except meraki.APIError as e:
            print(f"Error retrieving clients for Meraki switch {serial}: {e}")
            meraki_clients[serial] = []
    return meraki_clients

# Function to map Catalyst interfaces to Meraki ports
def map_catalyst_to_meraki_ports(mac_table, meraki_serials):
    mapping = []
    for entry in mac_table:
        catalyst_port = entry['port']
        vlan = entry['vlan']
        mac = entry['mac_address']

        # Extract the port number using InterfaceParser
        port_number = InterfaceParser.extract_port_number(catalyst_port, 'catalyst_generic')

        if port_number is None:
            print(f"Could not parse port name: {catalyst_port}")
            continue

        # Extract switch number from the interface name
        parsed = InterfaceParser.parse_interface(catalyst_port, 'catalyst_generic')
        if not parsed:
            print(f"Could not parse port name: {catalyst_port}")
            continue

        switch_number = int(parsed[1])  # Second element is switch number

        # Adjust switch_number to zero-based index
        meraki_index = switch_number - 1
        if meraki_index >= len(meraki_serials):
            print(f"No Meraki switch for Catalyst switch number {switch_number}")
            continue
        meraki_serial = meraki_serials[meraki_index]
        meraki_port_id = port_number

        mapping.append({
            'catalyst_port': catalyst_port,
            'meraki_serial': meraki_serial,
            'meraki_port_id': meraki_port_id,
            'vlan': vlan,
            'mac': mac,
        })
    return mapping

def clean_mac(mac_address):
    return ''.join(char for char in mac_address if char.isalnum())

# Function to compare MAC addresses and VLANs between Catalyst and Meraki switches
def compare_mac_addresses(mapping, meraki_clients):
    comparison_results = []
    for entry in mapping:
        mac = entry['mac'].lower()
        catalyst_vlan = entry['vlan']
        catalyst_port = entry['catalyst_port']
        meraki_serial = entry['meraki_serial']
        meraki_port_id = entry['meraki_port_id']

        # Find the client in Meraki clients
        clients = meraki_clients.get(meraki_serial, [])
        client_found = False
        for client in clients:
            client_mac = client.get('mac', '').lower()
            client_vlan = client.get('vlan', '')
            client_switchport = client.get('switchport', '')
            clean_client_mac_address = clean_mac(client_mac)
            clean_mac_address = clean_mac(mac)
            if clean_client_mac_address == clean_mac_address:
                client_found = True
                break

        if client_found:
            comparison_results.append({
                'MAC_Address': mac,
                'Catalyst_Port': catalyst_port,
                'Catalyst_VLAN': catalyst_vlan,
                'Meraki_Serial': meraki_serial,
                'Meraki_PortId': client_switchport,
                'Meraki_VLAN': client_vlan,
                'Status': 'Match' if str(meraki_port_id) == str(client_switchport) else 'Port Mismatch',
            })
        else:
            comparison_results.append({
                'MAC_Address': mac,
                'Catalyst_Port': catalyst_port,
                'Catalyst_VLAN': catalyst_vlan,
                'Meraki_Serial': meraki_serial,
                'Meraki_PortId': 'N/A',
                'Meraki_VLAN': 'N/A',
                'Status': 'Not Found in Meraki',
            })
    return comparison_results
 
def run(meraki_api_key, meraki_cloud_ids, catalyst_ip=None, catalyst_macs=None, name=None, credentials_list=None):
    """
    Main execution function to run the comparison between Catalyst and Meraki port statuses. Either the Catalyst switch IP or
    Catalyst interface statuses must be provided.

    Args:
        meraki_api_key (str): API key for accessing the Meraki Dashboard.
        meraki_cloud_ids (list): List of Meraki switch serials.
        catalyst_ip (str): IP address of the Catalyst switch (optional).
        catalyst_macs (list): List of Catalyst MAC address table entries (optional).
        name (str): Hostname of the Catalyst switch (optional).
        credentials_list (list, optional): List of credential dicts for Netmiko connection.

    Returns:
        tuple: A tuple containing comparison results and the Catalyst switch hostname.
    """
    # Use global credentials if credentials_list not provided (for backward compatibility)
    if credentials_list is None:
        credentials_list = credentials

    if catalyst_macs is None:
        if not catalyst_ip:
            print("Error: Either catalyst_ip or catalyst_macs must be provided.")
            return None, None

        print("Retrieving MAC address table from Catalyst switch...")
        macs_raw, name = get_running_config(
            ip_address=catalyst_ip,
            credentials=credentials_list,
            command='show mac address-table',
            use_textfsm=True,
            read_timeout=90
        )

        if not macs_raw:
            print("Failed to retrieve MAC address table from Catalyst switch.")
            return None, None

        # Convert to DataFrame and process
        macs_df = pd.DataFrame(macs_raw)
        macs_df.rename(columns={'destination_address': 'mac_address', 'destination_port': 'port', 'vlan_id': 'vlan'}, inplace=True)
        macs_df['port'] = macs_df['port'].apply(lambda x: x[0])
        macs_df = macs_df[['mac_address', 'vlan', 'port']]

        # Filter: Only GigabitEthernet ports
        catalyst_macs = macs_df[macs_df['port'].str.contains('Gi')]

        # Filter: Remove uplink ports using constant
        catalyst_macs = catalyst_macs[~catalyst_macs['port'].apply(
            lambda x: int(x.split('/')[2]) > UPLINK_PORT_THRESHOLD
        )]

        catalyst_macs.to_csv(f'{name}_macs_address_table.csv', index=False)
        catalyst_macs = catalyst_macs.to_dict('records')
        
    meraki_api_key = os.getenv("MERAKI_API_KEY")
    meraki_cloud_ids = meraki_cloud_ids
    target_device = {'IPAddress': catalyst_ip}
    print(f"Retrieved {len(catalyst_macs)} MAC address entries from Catalyst switch.")

    # Step 2: Get clients from Meraki switches
    print("Retrieving clients from Meraki switches...")
    meraki_clients = get_meraki_clients(meraki_api_key, meraki_cloud_ids)

    # Step 3: Map Catalyst ports to Meraki ports
    mapping = map_catalyst_to_meraki_ports(catalyst_macs, meraki_cloud_ids)
    print(f"Mapped {len(mapping)} Catalyst MAC entries to Meraki ports.")

    # Step 4: Compare MAC addresses and VLANs
    comparison_results = compare_mac_addresses(mapping, meraki_clients)
    pd.DataFrame(comparison_results).to_csv(f'{name}_mac_difs.csv', index=False)

    # Step 5: Output the comparison results
    print("\nMAC Address Comparison:")
    for result in comparison_results:
        print(f"MAC {result['MAC_Address']} on Catalyst {result['Catalyst_Port']} (VLAN {result['Catalyst_VLAN']}) "
              f"-> Meraki Switch {result['Meraki_Serial']} Port {result['Meraki_PortId']} (VLAN {result['Meraki_VLAN']}) "
              f"Status: {result['Status']}")
        
    comparison_results_df = pd.DataFrame(comparison_results)
    comparison_results_df.to_csv(f'{name}_mac_comparison.csv', index=False)
    return comparison_results, name
    

if __name__ == "__main__":
    # Example usage - DO NOT use hardcoded IPs in production
    # This is for testing only

    # Meraki API key, obtained from environment variables
    meraki_api_key = os.getenv("MERAKI_API_KEY")

    if not meraki_api_key:
        print("Error: MERAKI_API_KEY environment variable not set")
        sys.exit(1)

    print("This script should be called from the GUI or other controller.")
    print("Direct execution is not recommended.")

    