"""Demo data at realistic scale: agents, customers, tags, tickets and comments.

shortcut: rows are bulk-inserted with workflow-consistent states instead of calling
transition_to() per ticket (that would take many minutes on Neon). The DB constraints still
hold, and tests/test_seed.py checks the rule invariants on the output.
"""

import random
from datetime import datetime, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from tickets.models import SLA_HOURS, Agent, Comment, Customer, Tag, Ticket

S, P, C = Ticket.Status, Ticket.Priority, Ticket.Channel
SEED_PREFIX = "seed-"  # seeded agent users; --reset deletes only these, never real accounts
BATCH = 1000

FIRST = [
    "Anna",
    "Mart",
    "Liis",
    "Kaarel",
    "Eva",
    "Jaan",
    "Kati",
    "Rasmus",
    "Laura",
    "Markus",
    "Sofia",
    "Oskar",
    "Mia",
    "Robin",
    "Hanna",
    "Karl",
    "Elena",
    "Tomas",
    "Ida",
    "Mikk",
    "Sara",
    "Lukas",
    "Emma",
    "Joonas",
    "Nora",
]  # noqa: E501
LAST = [
    "Tamm",
    "Saar",
    "Sepp",
    "Mägi",
    "Kask",
    "Kukk",
    "Rebane",
    "Ilves",
    "Pärn",
    "Koppel",
    "Virtanen",
    "Korhonen",
    "Berzins",
    "Kazlauskas",
    "Lindqvist",
    "Novak",
    "Fischer",
    "Weber",
    "Nowak",
    "Jansen",
]  # noqa: E501
COMPANY_NAMES = [
    "Nordbyte", "Baltic Freight", "Tallinn Tea House", "Riga Robotics", "Vilnius Bikes",
    "Kalev Apps", "Saare Fish", "Helsinki Health", "Tartu Labs", "Pärnu Surf", "Narva Steel",
    "Lumi Games", "",
]  # fmt: skip
COUNTRIES = ["EE"] * 5 + ["FI", "FI", "LV", "LV", "LT", "SE", "DE", "PL", "GB", "NL"]
TAGS = [
    "billing", "refund", "invoice", "login", "password-reset", "2fa", "bug", "crash", "slow",
    "mobile", "ios", "android", "web", "api", "integration", "export", "import", "data-loss",
    "feature-request", "ux", "onboarding", "cancellation", "upgrade", "downgrade", "trial",
    "vat", "gdpr", "security", "email-delivery", "notifications", "sso", "permissions",
    "outage", "performance", "localisation", "accessibility", "pricing", "partner", "vip",
    "follow-up",
]  # fmt: skip
SUBJECTS = [
    "Can't log in after the latest update",
    "Charged twice for {month}",
    "Invoice shows the wrong VAT number",
    "Export to CSV times out",
    "App crashes when I open the {area} page",
    "How do I add a team member?",
    "Password reset email never arrives",
    "Refund for unused seats",
    "API returns 500 on {area}",
    "Two-factor code is always rejected",
    "Dashboard is very slow today",
    "Please cancel my subscription",
    "Data from yesterday is missing",
    "Request: dark mode in the mobile app",
    "SSO login loops back to the start",
    "Notifications stopped working on Android",
    "Wrong currency on the pricing page",
    "Upgrade to the annual plan",
    "Can you delete my account under GDPR?",
    "Import fails for files over 5 MB",
]
AREAS = ["billing", "reports", "settings", "projects", "team", "integrations"]
MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
]
CUSTOMER_LINES = [
    "This started this morning and nothing I try fixes it.",
    "It worked fine last week. Any idea what changed?",
    "We're a paying customer and this is blocking our team.",
    "Screenshot attached. Let me know if you need more details.",
    "Following up on this, is there any update?",
    "Thanks, that worked!",
    "Still happening for two of my colleagues.",
]
AGENT_LINES = [
    "Thanks for reporting this. I'm looking into it now.",
    "Could you tell me which browser and version you're using?",
    "I've reproduced it and passed it to engineering.",
    "A fix is live now. Could you check again?",
    "I've issued the refund; it shows in 3–5 business days.",
    "I've reset the setting on our side. Please try once more.",
]
INTERNAL_LINES = [
    "Known issue, linked to the payment-provider incident.",
    "Customer is on the enterprise plan; prioritise.",
    "Checked the logs: the request never reached our API.",
    "Escalated to tier 2.",
]
# Sample attachments, uploaded once and shared by every seeded comment that has one.
SAMPLES = {
    "seed-samples/screenshot.png": bytes.fromhex(
        "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
        "1f15c4890000000d49444154789c63f8cfc0f01f0005000201ffa0f5f4"
        "c00000000049454e44ae426082"
    ),
    "seed-samples/invoice.pdf": b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n",
    "seed-samples/app-log.txt": b"2026-10-14 09:12:03 ERROR export timed out after 30s\n",
}


class Command(BaseCommand):
    help = "Load demo data. --reset deletes existing demo data first (keeps real accounts)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--reset", action="store_true", help="Delete demo data first.")
        parser.add_argument(
            "--seed", type=int, default=42, help="Random seed (same seed, same data)."
        )
        parser.add_argument(
            "--tickets", type=int, default=25_000, help="How many tickets to create."
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if options["reset"]:
            self._reset()
        elif Ticket.objects.exists():
            raise CommandError("Demo data already exists. Run with --reset to replace it.")
        rng = random.Random(options["seed"])  # noqa: S311 (demo data, reproducible, not secret)
        now = timezone.now().replace(microsecond=0)
        with transaction.atomic():
            counts = self._seed(rng, now, options["tickets"])
        self.stdout.write(
            self.style.SUCCESS("Seeded " + ", ".join(f"{n} {k}" for k, n in counts.items()) + ".")
        )

    def _reset(self) -> None:
        with transaction.atomic():
            Comment.objects.all().delete()
            Ticket.objects.all().delete()
            Customer.objects.all().delete()
            Tag.objects.all().delete()
            seeded = get_user_model().objects.filter(username__startswith=SEED_PREFIX)
            Agent.objects.filter(user__in=seeded).delete()
            seeded.delete()

    def _seed(self, rng: random.Random, now: datetime, n_tickets: int) -> dict[str, int]:
        for name, data in SAMPLES.items():
            if not default_storage.exists(name):
                default_storage.save(name, ContentFile(data))
        sample_names = list(SAMPLES)

        User = get_user_model()
        users = User.objects.bulk_create(
            User(
                username=f"{SEED_PREFIX}{i:02d}",
                first_name=rng.choice(FIRST),
                last_name=rng.choice(LAST),
                password=make_password(None),  # cannot log in
            )
            for i in range(25)
        )
        Agent.objects.bulk_create(Agent(user=u, team=rng.choice(Agent.Team.values)) for u in users)
        agents = list(Agent.objects.select_related("user"))  # includes seed_users' demo accounts

        customers = Customer.objects.bulk_create(
            (
                Customer(
                    name=f"{first} {last}",
                    email=f"{first.lower()}.{last.lower()}.{i}@customer.example".replace("ä", "a"),
                    company=rng.choice(COMPANY_NAMES),
                    country=rng.choice(COUNTRIES),
                    created_at=now - timedelta(days=rng.randint(30, 720)),
                )
                for i, (first, last) in enumerate(
                    (rng.choice(FIRST), rng.choice(LAST)) for _ in range(max(n_tickets // 6, 1))
                )
            ),
            batch_size=BATCH,
        )
        tags = Tag.objects.bulk_create(Tag(name=name) for name in TAGS)

        # Workflow shape: a small new queue, open work under each agent's cap, the rest history.
        wip = {a.pk: 0 for a in agents}
        tickets: list[Ticket] = []
        plans: list[tuple[Agent | None, list[tuple[datetime, Agent | None, bool]]]] = []
        n_new = max(n_tickets // 100, 1)
        for i in range(n_tickets):
            priority = rng.choices(P.values, weights=[20, 50, 22, 8])[0]
            sla = timedelta(hours=SLA_HOURS[P(priority)])
            if i < n_new:
                status, age = S.NEW, timedelta(hours=rng.uniform(0.2, 40))
            elif i < n_new * 4:
                status, age = (
                    rng.choice([S.OPEN, S.OPEN, S.PENDING_CUSTOMER]),
                    timedelta(days=rng.uniform(0.2, 10)),
                )
            elif i < n_tickets // 10:
                status, age = S.RESOLVED, timedelta(days=rng.uniform(1, 14))
            else:
                status, age = S.CLOSED, timedelta(days=rng.uniform(3, 180))
            created = now - age

            assignee: Agent | None = None
            if status in (S.OPEN, S.PENDING_CUSTOMER):
                free = [a for a in agents if wip[a.pk] < a.max_open_tickets - 3]
                if not free:  # every agent near their cap: leave it in the queue
                    status = S.NEW
                else:
                    assignee = rng.choice(free)
                    wip[assignee.pk] += 1
            elif status != S.NEW:
                assignee = rng.choice(agents)

            ticket = Ticket(
                customer=rng.choice(customers),
                assignee=assignee,
                subject=rng.choice(SUBJECTS).format(
                    month=rng.choice(MONTHS), area=rng.choice(AREAS)
                ),
                description=" ".join(rng.sample(CUSTOMER_LINES, 2)),
                status=status,
                priority=priority,
                channel=rng.choices(C.values, weights=[50, 25, 10, 15])[0],
                created_at=created,
            )
            # Comments: (time, author, internal). The first public agent reply = first response.
            comments: list[tuple[datetime, Agent | None, bool]] = []
            answered = status in (S.RESOLVED, S.CLOSED, S.PENDING_CUSTOMER) or (
                status == S.OPEN and rng.random() < 0.7
            )
            if answered:
                late = rng.random() < 0.1  # about one in ten misses the first-response SLA
                delay = sla * (rng.uniform(1.1, 3) if late else rng.uniform(0.05, 0.9))
                first = min(created + delay, now - timedelta(minutes=5))
                ticket.first_response_at = max(first, created)
                comments.append((ticket.first_response_at, assignee, False))
                t = ticket.first_response_at
                for _ in range(rng.randint(0, 3)):
                    t = min(t + timedelta(hours=rng.uniform(0.5, 30)), now)
                    author = rng.choice([None, assignee, assignee])
                    comments.append((t, author, author is not None and rng.random() < 0.3))
                if status in (S.RESOLVED, S.CLOSED):
                    ticket.resolved_at = min(t + timedelta(hours=rng.uniform(0.5, 48)), now)
                    if status == S.CLOSED:
                        ticket.closed_at = min(
                            ticket.resolved_at + timedelta(days=rng.uniform(1, 7)), now
                        )
            elif rng.random() < 0.3:
                comments.append(
                    (min(created + timedelta(hours=rng.uniform(0.5, 5)), now), None, False)
                )
            tickets.append(ticket)
            plans.append((assignee, comments))

        Ticket.objects.bulk_create(tickets, batch_size=BATCH)

        comment_rows: list[Comment] = []
        tag_rows: list[Any] = []
        for ticket, (_, comments) in zip(tickets, plans, strict=True):
            for created_at, author, internal in comments:
                if author is None:
                    body = rng.choice(CUSTOMER_LINES)
                else:
                    body = rng.choice(INTERNAL_LINES if internal else AGENT_LINES)
                comment = Comment(
                    ticket=ticket,
                    author=author,
                    body=body,
                    is_internal=internal,
                    created_at=created_at,
                )
                if rng.random() < 0.05:
                    comment.attachment.name = rng.choice(sample_names)
                comment_rows.append(comment)
            for tag in rng.sample(tags, rng.randint(0, 3)):
                tag_rows.append(Ticket.tags.through(ticket_id=ticket.pk, tag_id=tag.pk))
        Comment.objects.bulk_create(comment_rows, batch_size=BATCH)
        Ticket.tags.through.objects.bulk_create(tag_rows, batch_size=BATCH)
        return {
            "agents": len(users),
            "customers": len(customers),
            "tags": len(tags),
            "tickets": len(tickets),
            "comments": len(comment_rows),
        }
