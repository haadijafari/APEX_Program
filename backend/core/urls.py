from core.settings.base import DEBUG

if DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
from apps.accounts.views import register
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth Routes
    path("accounts/register/", register, name="register"),
    path(
        "accounts/", include("django.contrib.auth.urls")
    ),  # Provides login, logout, password_change
    path("", include("apps.gate.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("tinymce/", include("tinymce.urls")),
]

if DEBUG:
    urlpatterns += debug_toolbar_urls()

    # WhiteNoise handles this now (enabled via runserver_nostatic in dev.py).
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# # [FIX] Keep serving Media files manually in dev (WhiteNoise doesn't handle these)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
