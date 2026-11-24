from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import JavaScriptCatalog

urlpatterns = [
    # Встроенная вьюха смены языка: POST /i18n/setlang/ (имя 'set_language')
    path('i18n/', include('django.conf.urls.i18n')),
    # Переводы для JavaScript: даёт gettext() и interpolate() в app.js (файл djangojs.po)
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('admin/', admin.site.urls),
    path('cart/', include('cart.urls', namespace = 'cart')),
    path('users/', include('users.urls', namespace='users')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('payment/', include('payment.urls', namespace='payment')),
    path('', include('main.urls', namespace='main')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)