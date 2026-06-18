from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Built-in Django admin (we can use this or our custom portal)
    path('django-admin/', admin.site.urls), 
    
    # Core Application Routes
    path('', include('tracker_app.urls')),
]