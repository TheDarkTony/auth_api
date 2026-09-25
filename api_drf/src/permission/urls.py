from django.urls import path

from .views import ListRolesView, ListAppResourcesView, ListPermissionsView, DetailPermissionView


# 3. Include the router URLs in the app's urlpatterns
urlpatterns = [
    path('roles', ListRolesView.as_view(), name='role-list'),
    path('resources', ListAppResourcesView.as_view(), name='app-resource-list'),
    path('permissions', ListPermissionsView.as_view(), name='permission-list'),
    path('permissions/<int:id>', DetailPermissionView.as_view(), name='permission-detail')
]
