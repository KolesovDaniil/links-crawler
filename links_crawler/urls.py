from django.contrib import admin
from django.urls import path

from crawler.views import LinksOnPageView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("get-nested-links/", LinksOnPageView.as_view(), name="get_nested_links"),
]
