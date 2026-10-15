import pytest


@pytest.fixture(autouse=True)
def _plain_static_storage(settings):
    # The manifest storage used in production needs `collectstatic` to have run.
    # Tests render templates without it, so swap in the plain backend.
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
