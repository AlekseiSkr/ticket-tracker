from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from core.assistant import assistant
from tickets.views import attachment

urlpatterns = [
    # Before admin.site.urls, whose catch-all would swallow it. admin_view: staff only, CSRF on.
    path("admin/assistant/", admin.site.admin_view(assistant), name="assistant"),
    path("admin/", admin.site.urls),
    # admin_view: staff login required, same session and redirect behaviour as the admin.
    path("attachments/<int:comment_id>/", admin.site.admin_view(attachment), name="attachment"),
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
]
