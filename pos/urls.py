from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path, include

# Import the function (change 'dashboard' to 'orders' if you put it there)
from dashboard.views import temp_create_superuser
# Temporary superuser creation (delete after use!)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('menu/', include('menu.urls')),
    path('inventory/', include('inventory.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('reports/', include('reports.urls')),
    path('expenses/', include('expenses.urls')),

    path('temp-create-admin/', temp_create_superuser, name='temp_create_admin'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "CAFETERIA POS Admin"
admin.site.site_title = "CAFETERIA POS"
admin.site.index_title = "Welcome to CAFETERIA POS Administration"