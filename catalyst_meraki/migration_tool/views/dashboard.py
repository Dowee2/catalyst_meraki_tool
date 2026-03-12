from django.shortcuts import render


def dashboard(request):
    """Render the main dashboard with task cards."""
    return render(request, 'migration_tool/dashboard.html')
