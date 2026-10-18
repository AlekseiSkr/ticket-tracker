"""Create or update the demo login accounts, one per role. Passwords come from env vars only."""

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand
from django.db import transaction

from config.env import require_env
from tickets.models import Agent

# username, first name, last name, group, password env var, team
ACCOUNTS = [
    ("lead", "Liisa", "Tamm", "Support Lead", "DEMO_LEAD_PASSWORD", Agent.Team.TIER_2),
    ("agent", "Mart", "Kask", "Agent", "DEMO_AGENT_PASSWORD", Agent.Team.TIER_1),
]


class Command(BaseCommand):
    help = "Create or update the demo 'lead' and 'agent' accounts (passwords from env)."

    def handle(self, *args: Any, **options: Any) -> None:
        User = get_user_model()
        with transaction.atomic():
            for username, first, last, group, env_var, team in ACCOUNTS:
                password = require_env(env_var)
                user, created = User.objects.get_or_create(username=username)
                user.first_name, user.last_name, user.is_staff = first, last, True
                validate_password(password, user)  # no weak demo passwords in production
                user.set_password(password)
                user.save()
                user.groups.set([Group.objects.get(name=group)])
                Agent.objects.get_or_create(user=user, defaults={"team": team})
                self.stdout.write(f"{'Created' if created else 'Updated'} {username} ({group}).")
