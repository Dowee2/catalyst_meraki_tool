from django.urls import path, include

urlpatterns = [
    path('', include('catalyst_meraki.migration_tool.urls')),
]
