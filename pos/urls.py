# pos/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import your main dashboard home view (root entry point)
from dashboard.views import home

# Import the first-time setup view from accounts app
from accounts.views import first_time_setup

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),

    # Root URL - this is now the main entry point (handles /)
    path('', home, name='home'),  # ← root goes directly to dashboard home view

    # App URLs
    path('accounts/', include('accounts.urls')),    # Login, logout, signup, etc.
    path('', include('dashboard.urls')),
    path('menu/', include('menu.urls')),
    path('inventory/', include('inventory.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('reports/', include('reports.urls')),
    path('expenses/', include('expenses.urls')),

    # First-time setup page (only shown if no superuser exists)
    path('setup/', first_time_setup, name='setup'),

]

# Serve media and static files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site title and header
admin.site.site_header = "CAFETERIA POS Admin"
admin.site.site_title = "CAFETERIA POS"
admin.site.index_title = "Welcome to CAFETERIA POS Administration"