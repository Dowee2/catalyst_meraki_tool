"""
Comparison wizard views - 3-step wizard for comparing Catalyst and Meraki switches.

Steps:
1. Capture - Enter Catalyst switch details and capture data (or use saved capture)
2. Meraki Details - Enter Meraki serial numbers
3. Results - View comparison results
"""

import re
from django.shortcuts import render, redirect
from django.contrib import messages

from utils.config_manager import get_api_key
from models.switch_data_model import SwitchDataModel


WIZARD_STEPS = ['Capture', 'Meraki', 'Compare']

_switch_data_model = SwitchDataModel()


def _get_wizard_data(request):
    """Get comparison wizard data from session."""
    return request.session.get('comparison_wizard', {
        'source_type': 'new',
        'catalyst_ip': '',
        'credential_index': None,
        'new_username': '',
        'new_password': '',
        'compare_interfaces': True,
        'compare_macs': True,
        'meraki_serials': [],
        'capture_task_id': None,
        'captured_hostname': '',
        'has_interface_data': False,
        'has_mac_data': False,
        'saved_interface_capture': '',
        'saved_mac_capture': '',
    })


def _set_wizard_data(request, data):
    """Save comparison wizard data to session."""
    request.session['comparison_wizard'] = data
    request.session.modified = True


def step_capture(request):
    """Step 1: Capture source data from Catalyst switch."""
    data = _get_wizard_data(request)
    credentials = request.session.get('credentials', [])

    # Get saved captures for dropdown
    interface_captures = _switch_data_model.get_saved_interface_captures()
    mac_captures = _switch_data_model.get_saved_mac_captures()

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'select_source':
            data['source_type'] = request.POST.get('source_type', 'new')
            _set_wizard_data(request, data)

        elif action == 'select_credential':
            cred_index = request.POST.get('credential_index')
            if cred_index is not None:
                data['credential_index'] = int(cred_index)
                _set_wizard_data(request, data)

        elif action == 'set_new_credential':
            username = request.POST.get('new_username', '').strip()
            password = request.POST.get('new_password', '')
            if username and password:
                data['new_username'] = username
                data['new_password'] = password
                data['credential_index'] = None
                _set_wizard_data(request, data)
                messages.success(request, f'Credentials set for {username}.')
            else:
                messages.error(request, 'Username and password are required.')

        elif action == 'save_settings':
            data['catalyst_ip'] = request.POST.get('catalyst_ip', '').strip()
            data['compare_interfaces'] = request.POST.get('compare_interfaces') == 'on'
            data['compare_macs'] = request.POST.get('compare_macs') == 'on'
            _set_wizard_data(request, data)

        elif action == 'use_saved':
            data['source_type'] = 'saved'
            data['saved_interface_capture'] = request.POST.get('saved_interface_capture', '')
            data['saved_mac_capture'] = request.POST.get('saved_mac_capture', '')
            data['has_interface_data'] = bool(data['saved_interface_capture'])
            data['has_mac_data'] = bool(data['saved_mac_capture'])
            _set_wizard_data(request, data)

            if not data['has_interface_data'] and not data['has_mac_data']:
                messages.error(request, 'Please select at least one saved capture.')
            else:
                return redirect('migration_tool:compare_meraki')

        elif action == 'next':
            if data.get('source_type') == 'saved':
                if data.get('has_interface_data') or data.get('has_mac_data'):
                    return redirect('migration_tool:compare_meraki')
                messages.error(request, 'Please select saved capture data.')
            else:
                if not data.get('has_interface_data') and not data.get('has_mac_data'):
                    messages.error(request, 'Please capture data from the switch first.')
                else:
                    return redirect('migration_tool:compare_meraki')

    return render(request, 'migration_tool/comparison/step_capture.html', {
        'data': data,
        'credentials': credentials,
        'interface_captures': interface_captures,
        'mac_captures': mac_captures,
        'steps': WIZARD_STEPS,
        'current_step': 1,
    })


def step_meraki(request):
    """Step 2: Meraki serial numbers."""
    data = _get_wizard_data(request)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'add_serial':
            serial = request.POST.get('new_serial', '').strip().upper()
            if serial:
                serials = data.get('meraki_serials', [])
                if serial not in serials:
                    serials.append(serial)
                    data['meraki_serials'] = serials
                    _set_wizard_data(request, data)
            else:
                messages.error(request, 'Please enter a serial number.')

        elif action == 'remove_serial':
            index = int(request.POST.get('serial_index', -1))
            serials = data.get('meraki_serials', [])
            if 0 <= index < len(serials):
                serials.pop(index)
                data['meraki_serials'] = serials
                _set_wizard_data(request, data)

        elif action == 'next':
            serials = data.get('meraki_serials', [])
            if not serials:
                messages.error(request, 'Please add at least one Meraki serial number.')
            else:
                _set_wizard_data(request, data)
                return redirect('migration_tool:compare_results')

    # Build summary
    summary_lines = []
    if data.get('source_type') == 'saved':
        summary_lines.append('Using saved capture data')
    else:
        if data.get('captured_hostname'):
            summary_lines.append(f"Source: {data['captured_hostname']} ({data.get('catalyst_ip', '')})")
        if data.get('has_interface_data'):
            summary_lines.append('Interface data captured')
        if data.get('has_mac_data'):
            summary_lines.append('MAC address data captured')

    return render(request, 'migration_tool/comparison/step_meraki.html', {
        'data': data,
        'summary_lines': summary_lines,
        'steps': WIZARD_STEPS,
        'current_step': 2,
    })


def step_results(request):
    """Step 3: Comparison results."""
    data = _get_wizard_data(request)
    api_key = get_api_key()

    return render(request, 'migration_tool/comparison/step_results.html', {
        'data': data,
        'api_key_set': bool(api_key),
        'steps': WIZARD_STEPS,
        'current_step': 3,
    })


def cancel_wizard(request):
    """Cancel the comparison wizard."""
    if 'comparison_wizard' in request.session:
        del request.session['comparison_wizard']
    return redirect('migration_tool:dashboard')
