from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('create/', views.expense_create, name='expense_create'),
    path('', views.expense_list, name='expense_list'),
    path('add/', views.expense_add, name='expense_add'),
    path('<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('export-csv/', views.expense_export_csv, name='expense_export_csv'),
    # add more later: list, detail, etc.
]