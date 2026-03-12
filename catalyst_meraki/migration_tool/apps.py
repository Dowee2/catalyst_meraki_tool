from django.apps import AppConfig


class MigrationToolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalyst_meraki.migration_tool'
    verbose_name = 'Catalyst to Meraki Migration Tool'
