"""
API views for background task management.

These views handle starting background tasks (conversion, capture, comparison)
and polling for their output/status via AJAX.
"""

import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_protect

from utils.config_manager import get_api_key
from utils.script_loader import ScriptLoader
from config.script_types import ScriptType
from catalyst_meraki.migration_tool.task_manager import start_task, get_task

# Load script modules once at import time
_script_loader = ScriptLoader()
_modules = _script_loader.load_scripts()


@require_POST
@csrf_protect
def start_conversion(request):
    """Start a conversion task in the background."""
    api_key = get_api_key()
    if not api_key:
        return JsonResponse({'error': 'Meraki API Key is not set. Please configure it in Settings.'})

    wizard_data = request.session.get('conversion_wizard', {})
    credentials = request.session.get('credentials', [])

    source_type = wizard_data.get('source_type', 'ip')
    meraki_serials = wizard_data.get('meraki_serials', [])

    if not meraki_serials:
        return JsonResponse({'error': 'No Meraki serial numbers configured.'})

    convert_module = _modules.get(ScriptType.CONVERT) if _modules else None
    if not convert_module:
        return JsonResponse({'error': 'Conversion module not loaded.'})

    if source_type == 'ip':
        catalyst_ip = wizard_data.get('catalyst_ip', '')
        if not catalyst_ip:
            return JsonResponse({'error': 'Catalyst switch IP is required.'})

        # Resolve credentials
        cred_index = wizard_data.get('credential_index')
        new_username = wizard_data.get('new_username', '')
        new_password = wizard_data.get('new_password', '')

        if cred_index is not None and 0 <= cred_index < len(credentials):
            cred = credentials[cred_index]
            creds_list = [{'username': cred['username'], 'password': cred['password']}]
        elif new_username and new_password:
            creds_list = [{'username': new_username, 'password': new_password}]
        else:
            return JsonResponse({'error': 'No credentials provided.'})

        def run_conversion():
            print(f"Connecting to Catalyst switch at {catalyst_ip}...")
            print("Interface format: Auto-detected")
            convert_module.run(
                meraki_api_key=api_key,
                meraki_cloud_ids=meraki_serials,
                catalyst_ip=catalyst_ip,
                credentials_list=creds_list,
            )
            print("\nConfiguration conversion completed.")

        task_id = start_task(run_conversion)

    else:
        # File source
        config_content = wizard_data.get('config_file_content', '')
        hostname = wizard_data.get('hostname', '')

        if not config_content:
            return JsonResponse({'error': 'Configuration file content is missing.'})

        def run_file_conversion():
            print(f"Converting configuration for {hostname}...")
            print("Interface format: Auto-detected")
            convert_module.run(
                meraki_api_key=api_key,
                meraki_cloud_ids=meraki_serials,
                catalyst_config=config_content,
            )
            print("\nConfiguration conversion completed.")

        task_id = start_task(run_file_conversion)

    return JsonResponse({'task_id': task_id})


@require_POST
@csrf_protect
def start_capture(request):
    """Start a data capture task from a Catalyst switch."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request body.'})

    catalyst_ip = body.get('catalyst_ip', '').strip()
    compare_interfaces = body.get('compare_interfaces', True)
    compare_macs = body.get('compare_macs', True)

    if not catalyst_ip:
        return JsonResponse({'error': 'Catalyst switch IP is required.'})

    wizard_data = request.session.get('comparison_wizard', {})
    credentials_list = request.session.get('credentials', [])

    # Resolve credentials
    cred_index = wizard_data.get('credential_index')
    new_username = wizard_data.get('new_username', '')
    new_password = wizard_data.get('new_password', '')

    if cred_index is not None and 0 <= cred_index < len(credentials_list):
        cred = credentials_list[cred_index]
        creds = [{'username': cred['username'], 'password': cred['password']}]
    elif new_username and new_password:
        creds = [{'username': new_username, 'password': new_password}]
    else:
        return JsonResponse({'error': 'No credentials configured. Please select or enter credentials.'})

    # Save settings to session
    wizard_data['catalyst_ip'] = catalyst_ip
    wizard_data['compare_interfaces'] = compare_interfaces
    wizard_data['compare_macs'] = compare_macs
    request.session['comparison_wizard'] = wizard_data
    request.session.modified = True

    # We need a mutable reference to update session after capture completes
    session_key = request.session.session_key

    def do_capture():
        from utils.netmiko_utils import get_running_config
        import pandas as pd

        results = {'hostname': '', 'interfaces': None, 'macs': None}

        if compare_interfaces:
            print(f"Capturing interface status from {catalyst_ip}...")
            interface_data, hostname = get_running_config(
                ip_address=catalyst_ip,
                credentials=creds,
                command='show ip int brief',
                use_textfsm=True,
                read_timeout=60,
            )
            results['interfaces'] = interface_data
            results['hostname'] = hostname
            print(f"Retrieved {len(interface_data) if interface_data else 0} interfaces from {hostname}.")

        if compare_macs:
            print(f"Capturing MAC address table from {catalyst_ip}...")
            macs_raw, hostname = get_running_config(
                ip_address=catalyst_ip,
                credentials=creds,
                command='show mac address-table',
                use_textfsm=True,
                read_timeout=90,
            )
            if macs_raw:
                macs_df = pd.DataFrame(macs_raw)
                if not macs_df.empty:
                    macs_df.rename(columns={
                        'destination_address': 'mac_address',
                        'destination_port': 'port',
                        'vlan_id': 'vlan'
                    }, inplace=True)
                    if 'port' in macs_df.columns:
                        macs_df['port'] = macs_df['port'].apply(lambda x: x[0] if isinstance(x, list) else x)
                    macs_df = macs_df[['mac_address', 'vlan', 'port']]
                results['macs'] = macs_df
                if not results['hostname']:
                    results['hostname'] = hostname
                print(f"Retrieved {len(macs_df)} MAC entries.")

        interface_count = len(results['interfaces']) if results['interfaces'] else 0
        mac_count = len(results['macs']) if results['macs'] is not None else 0
        print(f"\nCapture completed for {results['hostname']}!")
        print(f"  - Interfaces: {interface_count}")
        print(f"  - MAC addresses: {mac_count}")

        return results

    task_id = start_task(do_capture)
    return JsonResponse({'task_id': task_id})


@require_POST
@csrf_protect
def start_comparison(request):
    """Start a comparison task."""
    api_key = get_api_key()
    if not api_key:
        return JsonResponse({'error': 'Meraki API Key is not set.'})

    wizard_data = request.session.get('comparison_wizard', {})
    meraki_serials = wizard_data.get('meraki_serials', [])

    if not meraki_serials:
        return JsonResponse({'error': 'No Meraki serial numbers configured.'})

    compare_intf_module = _modules.get(ScriptType.COMPARE_INTERFACES) if _modules else None
    compare_mac_module = _modules.get(ScriptType.COMPARE_MAC) if _modules else None

    # For now, run with available data
    # In a full implementation, we'd retrieve captured data from session/files

    def do_comparison():
        results = {'interfaces': None, 'macs': None}

        if compare_intf_module:
            print("Comparing port status...")
            try:
                intf_results, _ = compare_intf_module.run(
                    meraki_api_key=api_key,
                    meraki_cloud_ids=meraki_serials,
                    catalyst_ip=None,
                    catalyst_interfaces=None,
                    name=wizard_data.get('captured_hostname', 'Unknown'),
                    credentials_list=None,
                )
                results['interfaces'] = intf_results
            except Exception as e:
                print(f"Interface comparison error: {e}")

        if compare_mac_module:
            print("Comparing connected devices...")
            try:
                mac_results, _ = compare_mac_module.run(
                    meraki_api_key=api_key,
                    meraki_cloud_ids=meraki_serials,
                    catalyst_ip=None,
                    catalyst_macs=None,
                    name=wizard_data.get('captured_hostname', 'Unknown'),
                    credentials_list=None,
                )
                results['macs'] = mac_results
            except Exception as e:
                print(f"MAC comparison error: {e}")

        print("\nComparison completed!")
        return results

    task_id = start_task(do_comparison)
    return JsonResponse({'task_id': task_id})


@require_GET
def poll_task(request, task_id):
    """Poll a background task for new output and status."""
    task = get_task(task_id)
    if not task:
        return JsonResponse({'error': 'Task not found.'}, status=404)

    new_output = task.get_new_output()

    response = {
        'status': task.status,
        'output': new_output,
    }

    if task.status == 'completed':
        result = task.result
        # Serialize result if it contains DataFrames or complex objects
        if result and isinstance(result, dict):
            serialized = {}
            for key, value in result.items():
                if hasattr(value, 'to_dict'):
                    serialized[key] = value.to_dict('records')
                elif isinstance(value, list):
                    serialized[key] = value
                else:
                    serialized[key] = value
            response['result'] = serialized
    elif task.status == 'error':
        response['error'] = task.error

    return JsonResponse(response)
