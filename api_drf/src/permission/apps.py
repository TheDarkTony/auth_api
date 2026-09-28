from django.apps import AppConfig


class PermissionConfig(AppConfig):
    name = 'src.permission'
    label = 'permission'
    verbose_name = 'Permission management'
    default = True
