# pos/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Main dashboard home view (root entry point)
from dashboard.views import home

# First-time setup view from accounts app
from accounts.views import first_time_setup

urlpatterns = [
    # -------------------------
    # ADMIN SITE
    # -------------------------
    path('admin/', admin.site.urls),

    # -------------------------
    # ROOT / DASHBOARD
    # -------------------------
    path('', home, name='home'),  # Dashboard home view at root

    # -------------------------
    # APP URLS
    # -------------------------
    path('accounts/', include('accounts.urls')),   # Login, logout, signup, etc.
    path('', include('dashboard.urls')),           # Dashboard pages
    path('menu/', include('menu.urls')),           # Menu management
    path('inventory/', include('inventory.urls')), # Inventory management
    path('orders/', include('orders.urls')),       # Orders management
    path('payments/', include('payments.urls')),   # Payment processing & credit sales
    path('reports/', include('reports.urls')),     # Reports module
    path('expenses/', include('expenses.urls')),   # Expenses module

    # -------------------------
    # FIRST-TIME SETUP
    # -------------------------
    path('setup/', first_time_setup, name='setup'),  # Shown only if no superuser exists
]

# -------------------------
# SERVE MEDIA AND STATIC FILES (DEVELOPMENT ONLY)
# -------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# -------------------------
# CUSTOMIZE ADMIN SITE TITLES
# -------------------------
admin.site.site_header = "CAFETERIA POS Admin"
admin.site.site_title = "CAFETERIA POS"
admin.site.index_title = "Welcome to CAFETERIA POS Administration"