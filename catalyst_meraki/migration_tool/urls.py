from django.urls import path
from .views import dashboard, settings, conversion, comparison, api

app_name = 'migration_tool'

urlpatterns = [
    # Dashboard
    path('', dashboard.dashboard, name='dashboard'),

    # Settings
    path('settings/', settings.settings_view, name='settings'),
    path('settings/api-key/', settings.save_api_key_view, name='save_api_key'),
    path('settings/credentials/', settings.manage_credentials, name='manage_credentials'),
    path('settings/credentials/add/', settings.add_credential, name='add_credential'),
    path('settings/credentials/<int:index>/delete/', settings.delete_credential, name='delete_credential'),

    # Conversion wizard
    path('migrate/', conversion.step_source, name='convert_source'),
    path('migrate/credentials/', conversion.step_credentials, name='convert_credentials'),
    path('migrate/destination/', conversion.step_destination, name='convert_destination'),
    path('migrate/review/', conversion.step_review, name='convert_review'),
    path('migrate/cancel/', conversion.cancel_wizard, name='convert_cancel'),

    # Comparison wizard
    path('compare/', comparison.step_capture, name='compare_capture'),
    path('compare/meraki/', comparison.step_meraki, name='compare_meraki'),
    path('compare/results/', comparison.step_results, name='compare_results'),
    path('compare/cancel/', comparison.cancel_wizard, name='compare_cancel'),

    # API endpoints for background tasks
    path('api/task/start-conversion/', api.start_conversion, name='api_start_conversion'),
    path('api/task/start-capture/', api.start_capture, name='api_start_capture'),
    path('api/task/start-comparison/', api.start_comparison, name='api_start_comparison'),
    path('api/task/<str:task_id>/poll/', api.poll_task, name='api_poll_task'),
]
