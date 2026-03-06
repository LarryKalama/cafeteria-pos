from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('items/', views.menuitem_list, name='menuitem_list'),
    path('items/create/', views.menuitem_create, name='item_create'),
    path('items/<int:pk>/update/', views.menuitem_update, name='item_update'),
    path('items/<int:pk>/delete/', views.menuitem_delete, name='item_delete'),

# Category management
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),



]