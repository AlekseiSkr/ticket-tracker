"""Create or update the reviewer logins: a Lead and an Agent account for each reviewer.

Benrey asked for pre-made accounts for two reviewers (no self-signup). Every account has its
own password, read from an env var, so neither reviewer holds the other's credentials.
"""

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand
from django.db import transaction

from config.env import require_env
from tickets.models import Agent

REVIEWERS = 2
# role suffix, group, team, display last name
ROLES = [
    ("lead", "Support Lead", Agent.Team.TIER_2, "Lead"),
    ("agent", "Agent", Agent.Team.TIER_1, "Agent"),
]


class Command(BaseCommand):
    help = "Create or update lead-1/agent-1 and lead-2/agent-2 (DEMO_<ROLE>_<N>_PASSWORD)."

    def handle(self, *args: Any, **options: Any) -> None:
        User = get_user_model()
        with transaction.atomic():
            for n in range(1, REVIEWERS + 1):
                for role, group, team, last in ROLES:
                    username = f"{role}-{n}"
                    password = require_env(f"DEMO_{role.upper()}_{n}_PASSWORD")
                    user, created = User.objects.get_or_create(username=username)
                    user.first_name, user.last_name = f"Reviewer {n}", last
                    user.is_staff = True
                    validate_password(password, user)  # no weak demo passwords in production
                    user.set_password(password)
                    user.save()
                    user.groups.set([Group.objects.get(name=group)])
                    Agent.objects.get_or_create(user=user, defaults={"team": team})
                    self.stdout.write(
                        f"{'Created' if created else 'Updated'} {username} ({group})."
                    )
