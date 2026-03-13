"""
Accounts App URLs
"""
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    # Custom login view (original implementation - restored since it worked before)
path("login/", auth_views.LoginView.as_view(
        template_name="accounts/login.html"
    ), name="login"),

    # All other paths - unchanged
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/update/', views.user_update, name='user_update'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
]