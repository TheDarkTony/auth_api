from django.apps import AppConfig


class IdentityConfig(AppConfig):
    name = 'src.identity'
    label = 'identity'
    verbose_name = 'Identity management'
    default = True
