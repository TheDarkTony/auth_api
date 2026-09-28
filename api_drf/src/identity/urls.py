from django.urls import path

from .views import ListIdentitiesView, DetailIdentityView, ListUsersView, DetailUserView, DetailProfileView, change_user_pwd


urlpatterns = [
    path('identities', ListIdentitiesView.as_view(), name='identity-list'),
    path('identities/<int:id>', DetailIdentityView.as_view(), name='identity-details'),
    path('users', ListUsersView.as_view(), name='user-list'),
    path('users/<int:id>', DetailUserView.as_view(), name='user-details'),
    path('profile', DetailProfileView.as_view(), name='profile-details'),
    path('profile/credentials/pwd', change_user_pwd, name='profile-credentials-edit')
]
