from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include

urlpatterns = [
    path("api/v1/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/v1/", include("core.api_core.urls")),
    path("i18n/", include("django.conf.urls.i18n")),  # set_language in Navbar
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__", include(debug_toolbar.urls))]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("core.urls", namespace="core")),
    path("", include("order.urls", namespace="order")),
    path("", include("checkout.urls", namespace="checkout")),
    path("payment/", include("payment.urls", namespace="payment")),
)
