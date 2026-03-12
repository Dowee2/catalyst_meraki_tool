"""
Conversion wizard views - 4-step wizard for migrating Catalyst to Meraki.

Steps:
1. Source - Choose IP connection or config file
2. Credentials - Enter/select login credentials (skipped for file source)
3. Destination - Enter Meraki serial numbers
4. Review & Execute - Summary and run migration
"""

import os
from django.shortcuts import render, redirect
from django.contrib import messages

from utils.config_manager import get_api_key


WIZARD_STEPS = ['Source', 'Login', 'Destination', 'Migrate']


def _get_wizard_data(request):
    """Get conversion wizard data from session."""
    return request.session.get('conversion_wizard', {
        'source_type': 'ip',
        'catalyst_ip': '',
        'config_file_path': '',
        'config_file_content': '',
        'hostname': '',
        'credential_index': None,
        'new_username': '',
        'new_password': '',
        'meraki_serials': [],
    })


def _set_wizard_data(request, data):
    """Save conversion wizard data to session."""
    request.session['conversion_wizard'] = data
    request.session.modified = True


def step_source(request):
    """Step 1: Source selection - IP or file."""
    data = _get_wizard_data(request)

    if request.method == 'POST':
        source_type = request.POST.get('source_type', 'ip')
        data['source_type'] = source_type

        if source_type == 'ip':
            catalyst_ip = request.POST.get('catalyst_ip', '').strip()
            if not catalyst_ip:
                messages.error(request, 'Please enter the switch IP address.')
                return render(request, 'migration_tool/conversion/step_source.html', {
                    'data': data, 'steps': WIZARD_STEPS, 'current_step': 1,
                })
            data['catalyst_ip'] = catalyst_ip
        else:
            config_file = request.FILES.get('config_file')
            hostname = request.POST.get('hostname', '').strip()

            if not config_file:
                messages.error(request, 'Please select a configuration file.')
                return render(request, 'migration_tool/conversion/step_source.html', {
                    'data': data, 'steps': WIZARD_STEPS, 'current_step': 1,
                })
            if not hostname:
                messages.error(request, 'Please enter the switch hostname.')
                return render(request, 'migration_tool/conversion/step_source.html', {
                    'data': data, 'steps': WIZARD_STEPS, 'current_step': 1,
                })

            try:
                data['config_file_content'] = config_file.read().decode('utf-8')
                data['config_file_path'] = config_file.name
            except Exception as e:
                messages.error(request, f'Failed to read config file: {e}')
                return render(request, 'migration_tool/conversion/step_source.html', {
                    'data': data, 'steps': WIZARD_STEPS, 'current_step': 1,
                })

            data['hostname'] = hostname

        _set_wizard_data(request, data)

        # Skip credentials step for file source
        if source_type == 'file':
            return redirect('migration_tool:convert_destination')
        return redirect('migration_tool:convert_credentials')

    return render(request, 'migration_tool/conversion/step_source.html', {
        'data': data,
        'steps': WIZARD_STEPS,
        'current_step': 1,
    })


def step_credentials(request):
    """Step 2: Credentials selection/entry."""
    data = _get_wizard_data(request)

    # Skip if file source
    if data.get('source_type') == 'file':
        return redirect('migration_tool:convert_destination')

    credentials = request.session.get('credentials', [])

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'use_saved':
            cred_index = request.POST.get('credential_index')
            if cred_index is not None:
                cred_index = int(cred_index)
                if 0 <= cred_index < len(credentials):
                    data['credential_index'] = cred_index
                    data['new_username'] = ''
                    data['new_password'] = ''
                    _set_wizard_data(request, data)
                    return redirect('migration_tool:convert_destination')
            messages.error(request, 'Please select a credential.')

        elif action == 'use_new':
            username = request.POST.get('new_username', '').strip()
            password = request.POST.get('new_password', '')
            if not username or not password:
                messages.error(request, 'Please enter both username and password.')
            else:
                data['new_username'] = username
                data['new_password'] = password
                data['credential_index'] = None
                _set_wizard_data(request, data)
                return redirect('migration_tool:convert_destination')

    return render(request, 'migration_tool/conversion/step_credentials.html', {
        'data': data,
        'credentials': credentials,
        'steps': WIZARD_STEPS,
        'current_step': 2,
    })


def step_destination(request):
    """Step 3: Meraki serial numbers."""
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
                    messages.warning(request, 'Serial number already added.')
            else:
                messages.error(request, 'Please enter a serial number.')

        elif action == 'remove_serial':
            index = int(request.POST.get('serial_index', -1))
            serials = data.get('meraki_serials', [])
            if 0 <= index < len(serials):
                serials.pop(index)
                data['meraki_serials'] = serials
                _set_wizard_data(request, data)

        elif action == 'import_serials':
            raw = request.POST.get('import_text', '')
            import re
            new_serials = [s.strip().upper() for s in re.split(r'[,\n\r]+', raw) if s.strip()]
            if new_serials:
                serials = data.get('meraki_serials', [])
                for s in new_serials:
                    if s not in serials:
                        serials.append(s)
                data['meraki_serials'] = serials
                _set_wizard_data(request, data)

        elif action == 'move_up':
            index = int(request.POST.get('serial_index', -1))
            serials = data.get('meraki_serials', [])
            if 0 < index < len(serials):
                serials[index], serials[index - 1] = serials[index - 1], serials[index]
                data['meraki_serials'] = serials
                _set_wizard_data(request, data)

        elif action == 'move_down':
            index = int(request.POST.get('serial_index', -1))
            serials = data.get('meraki_serials', [])
            if 0 <= index < len(serials) - 1:
                serials[index], serials[index + 1] = serials[index + 1], serials[index]
                data['meraki_serials'] = serials
                _set_wizard_data(request, data)

        elif action == 'next':
            serials = data.get('meraki_serials', [])
            if not serials:
                messages.error(request, 'Please add at least one Meraki serial number.')
            else:
                _set_wizard_data(request, data)
                return redirect('migration_tool:convert_review')

        # Stay on the same page for serial management actions
        return render(request, 'migration_tool/conversion/step_destination.html', {
            'data': data, 'steps': WIZARD_STEPS, 'current_step': 3,
        })

    return render(request, 'migration_tool/conversion/step_destination.html', {
        'data': data,
        'steps': WIZARD_STEPS,
        'current_step': 3,
    })


def step_review(request):
    """Step 4: Review and execute migration."""
    data = _get_wizard_data(request)
    credentials = request.session.get('credentials', [])

    # Build summary
    summary = {}
    if data.get('source_type') == 'ip':
        summary['source'] = f"Connect to switch at {data.get('catalyst_ip', '')}"
        if data.get('credential_index') is not None and data['credential_index'] < len(credentials):
            cred = credentials[data['credential_index']]
            summary['login'] = cred.get('username', 'N/A')
        elif data.get('new_username'):
            summary['login'] = data['new_username']
        else:
            summary['login'] = 'N/A'
    else:
        summary['source'] = 'Configuration file'
        summary['file'] = data.get('config_file_path', '')
        summary['hostname'] = data.get('hostname', '')

    summary['serials'] = data.get('meraki_serials', [])
    summary['interface_format'] = 'Auto-detected from configuration'

    return render(request, 'migration_tool/conversion/step_review.html', {
        'data': data,
        'summary': summary,
        'steps': WIZARD_STEPS,
        'current_step': 4,
    })


def cancel_wizard(request):
    """Cancel the conversion wizard and return to dashboard."""
    if 'conversion_wizard' in request.session:
        del request.session['conversion_wizard']
    return redirect('migration_tool:dashboard')
