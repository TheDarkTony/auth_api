from django.apps import AppConfig


class AuthConfig(AppConfig):
    name = 'src.auth'
    label = 'sign'
    verbose_name = 'Sign in/up management'
    default = True
