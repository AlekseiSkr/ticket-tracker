import pytest
from django.contrib import admin
from django.contrib.auth.models import Group, User
from unfold.admin import ModelAdmin

from core.admin_ui import environment_callback


@pytest.mark.django_db
def test_login_page_renders_the_benrey_theme(client):
    html = client.get("/admin/login/", secure=True).content.decode()
    assert 'class="dark"' in html  # dark only
    assert "--color-primary-600: rgb(195, 255, 0)" in html  # lime signal (#c3ff00) fills buttons
    assert "core/theme.css" in html
    assert "core/favicon.svg" in html
    assert "core/login-panel.svg" in html
    assert "fonts.googleapis.com" not in html  # fonts are self-hosted
    assert "Return to site" not in html  # "/" only redirects back here


@pytest.mark.django_db
def test_dashboard_has_skip_link_and_greeting(admin_client):
    html = admin_client.get("/admin/", secure=True).content.decode()
    assert html.index('class="skip-link"') < html.index('id="nav-sidebar')
    assert "Welcome back, admin." in html


def test_auth_admins_use_unfold():
    assert isinstance(admin.site._registry[User], ModelAdmin)
    assert isinstance(admin.site._registry[Group], ModelAdmin)


@pytest.mark.django_db
def test_user_change_page_renders(admin_client, admin_user):
    response = admin_client.get(f"/admin/auth/user/{admin_user.pk}/change/", secure=True)
    assert response.status_code == 200


@pytest.mark.django_db
def test_404_page_is_branded(client):
    response = client.get("/no-such-page/", secure=True)
    assert response.status_code == 404
    html = response.content.decode()
    assert "This page doesn&#x27;t exist." in html or "This page doesn't exist." in html
    assert 'href="/admin/"' in html


def test_environment_badge_only_when_debug(settings, rf):
    settings.DEBUG = False
    assert environment_callback(rf.get("/")) is None
    settings.DEBUG = True
    assert environment_callback(rf.get("/")) == ["Local", "info"]
