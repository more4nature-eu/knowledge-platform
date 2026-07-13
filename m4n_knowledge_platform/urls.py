from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from django.contrib import admin
from django.views.generic import TemplateView

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail_footnotes import urls as footnotes_urls

from m4n_knowledge_platform.search import views as search_views
from m4n_knowledge_platform import views

from m4n_knowledge_platform.needs_and_solutions_hub import urls as needs_and_solutions_hub_urls

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("search/", search_views.search, name="search"),
    path("footnotes/", include(footnotes_urls)),
    path("newsletter/signup/", views.mailchimp_newsletter_signup, name="mailchimp_newsletter_signup"),
    path("needs-and-solutions-hub/", include(needs_and_solutions_hub_urls))
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# These URLs will be available under a language code prefix only for languages that
# are not set as default in LANGUAGE_CODE.

urlpatterns = urlpatterns + i18n_patterns(
    path('search/', search_views.search, name='search'),
    path("", include(wagtail_urls)),
    prefix_default_language=False,
)

