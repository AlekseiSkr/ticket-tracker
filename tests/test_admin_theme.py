import pytest


@pytest.mark.django_db
def test_admin_renders_the_benrey_theme(client):
    html = client.get("/admin/login/", secure=True).content.decode()
    assert 'class="dark"' in html  # dark only
    assert "--color-primary-600: rgb(195, 255, 0)" in html  # lime signal (#c3ff00) fills buttons
    assert "core/theme.css" in html
    assert "family=Geist" in html
