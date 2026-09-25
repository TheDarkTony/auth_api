from django.urls import path
from .views import signup, signup_2fa, signin, signin_2fa, signout


urlpatterns = [
    path('auth/signup', signup, name='auth-signup'),
    path('auth/signup/second_factor', signup_2fa, name='auth-signup-2fa'),
    path('auth/signin', signin, name='auth-signin'),
    path('auth/signin/second_factor', signin_2fa, name='auth-signin-2fa'),
    path('auth/signout0', signout, name='auth-signout')
]
