from unittest import mock

import pytest
from django.db.utils import OperationalError


@pytest.mark.django_db
def test_healthz_never_touches_the_database(client, django_assert_num_queries):
    with django_assert_num_queries(0):
        response = client.get("/healthz", HTTP_HOST="unlisted-host.internal")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_readyz_reports_database_up(client):
    response = client.get("/readyz", HTTP_HOST="unlisted-host.internal")
    assert response.status_code == 200
    assert response.json()["database"] == "up"


def test_readyz_returns_503_when_database_is_down(client):
    with mock.patch("core.middleware.connection.cursor", side_effect=OperationalError("down")):
        response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json()["database"] == "down"


@pytest.mark.django_db
def test_admin_login_page_renders(client):
    response = client.get("/admin/login/")
    assert response.status_code == 200
