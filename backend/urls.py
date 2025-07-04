from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.http import HttpResponse


def home(request):
    return HttpResponse("""
                   <h1>Yabuwat Atelier</h1>
                   <a href="/admin/">Admin Page</a>              
                       """)


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('adm/', include('admin_api.urls'))
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
