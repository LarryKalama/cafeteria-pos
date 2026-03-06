from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Main stock list (root of inventory app)
    path('', views.stock_list, name='stock_list'),

    # Add / receive new stock
    path('add/', views.stock_add, name='stock_add'),

    # Edit existing stock record
    path('<int:pk>/edit/', views.stock_edit, name='stock_edit'),

    # Delete stock entry
    path('<int:pk>/delete/', views.stock_delete, name='stock_delete'),

    # Quick adjustment (add or remove quantity) for a specific stock
    path('stock/<int:pk>/adjust/', views.stock_adjust, name='stock_adjust'),

    # View transaction history for a specific stock item
    path('stock/<int:pk>/transactions/', views.stock_transactions, name='stock_transactions'),
]