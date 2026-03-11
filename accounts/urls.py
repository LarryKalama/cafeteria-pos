"""
Accounts App URLs
"""
from django.urls import path
from django.contrib.auth.views import LoginView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Use Django's built-in LoginView with custom template (fixes 500 error)
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),

    # Existing paths - unchanged
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/update/', views.user_update, name='user_update'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
]