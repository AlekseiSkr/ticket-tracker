import pytest
from django.contrib.auth.models import Group, User

from tickets.models import Agent, Customer


@pytest.fixture(autouse=True)
def _plain_static_storage(settings):
    # The manifest storage used in production needs `collectstatic` to have run.
    # Tests render templates without it, so swap in the plain backend.
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


# Shared by test_tickets.py and test_assistant.py.
def make_user(username: str, group: str) -> User:
    user = User.objects.create_user(username, password="x", is_staff=True, first_name=username)
    user.groups.add(Group.objects.get(name=group))
    Agent.objects.create(user=user)
    return User.objects.get(pk=user.pk)  # fresh instance: no cached permissions


@pytest.fixture
def lead(db):
    return make_user("lea", "Support Lead")


@pytest.fixture
def agent(db):
    return make_user("mart", "Agent")


@pytest.fixture
def other_agent(db):
    return make_user("kati", "Agent")


@pytest.fixture
def customer(db):
    return Customer.objects.create(name="Anna Saar", email="anna@customer.example")
