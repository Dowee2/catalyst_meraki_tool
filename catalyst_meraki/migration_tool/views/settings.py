from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from utils.config_manager import get_api_key, save_api_key


def _get_credentials(request):
    """Get credentials list from session."""
    return request.session.get('credentials', [])


def _set_credentials(request, creds):
    """Save credentials list to session."""
    request.session['credentials'] = creds


def settings_view(request):
    """Render the settings page."""
    api_key = get_api_key()
    credentials = _get_credentials(request)

    return render(request, 'migration_tool/settings.html', {
        'api_key': api_key,
        'credentials': credentials,
        'api_key_set': bool(api_key),
    })


@require_POST
def save_api_key_view(request):
    """Save the Meraki API key."""
    api_key = request.POST.get('api_key', '').strip()

    if not api_key:
        messages.error(request, 'API Key cannot be empty.')
        return redirect('migration_tool:settings')

    save_api_key(api_key)
    messages.success(request, 'API Key saved successfully.')
    return redirect('migration_tool:settings')


@require_POST
def manage_credentials(request):
    """Bulk update credentials from form."""
    # This is handled via add/delete individual endpoints
    return redirect('migration_tool:settings')


@require_POST
def add_credential(request):
    """Add a new credential."""
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    description = request.POST.get('description', '').strip()

    if not username or not password:
        messages.error(request, 'Username and password are required.')
        return redirect('migration_tool:settings')

    if not description:
        description = f"{username} credential"

    creds = _get_credentials(request)
    creds.append({
        'username': username,
        'password': password,
        'description': description,
    })
    _set_credentials(request, creds)
    messages.success(request, f'Credential for {username} added.')
    return redirect('migration_tool:settings')


@require_POST
def delete_credential(request, index):
    """Delete a credential by index."""
    creds = _get_credentials(request)
    if 0 <= index < len(creds):
        removed = creds.pop(index)
        _set_credentials(request, creds)
        messages.success(request, f'Credential for {removed["username"]} removed.')
    else:
        messages.error(request, 'Invalid credential index.')
    return redirect('migration_tool:settings')
