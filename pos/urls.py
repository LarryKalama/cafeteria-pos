# pos/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import the setup view from accounts app
from accounts.views import first_time_setup

# Import the temporary superuser view from dashboard app
from dashboard.views import temp_create_superuser

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),

    # App URLs
    path('', include('dashboard.urls')),          # Dashboard / home
    path('accounts/', include('accounts.urls')),  # Login, logout, etc.
    path('menu/', include('menu.urls')),
    path('inventory/', include('inventory.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('reports/', include('reports.urls')),
    path('expenses/', include('expenses.urls')),

    # First-time setup page (only shows if no superuser exists)
    path('setup/', first_time_setup, name='setup'),

    # Temporary superuser creation endpoint (delete after first admin is created!)
    path('temp-create-admin/', temp_create_superuser, name='temp_create_admin'),
]

# Serve media and static files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site title and header
admin.site.site_header = "CAFETERIA POS Admin"
admin.site.site_title = "CAFETERIA POS"
admin.site.index_title = "Welcome to CAFETERIA POS Administration"