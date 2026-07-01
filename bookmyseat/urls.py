from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('users/', include('users.urls')),
    path('movies/', include('movies.urls')),
    path('',include('movies.urls')),
]
if settings.DEBUG:
    # serve media files uploaded by users
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # serve static files (css, js, images) during development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)