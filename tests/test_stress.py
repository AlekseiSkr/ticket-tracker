"""On-demand stress test: seeds demo data at scale, then measures the admin under it.

Not part of the normal suite or CI. Run it with:

    docker compose exec -e STRESS_TICKETS=25000 web pytest -m stress -s

STRESS_TICKETS sets the seed size (default 25000) and STRESS_P95_MS the latency budget every
page must stay under (default 1500). It uses pytest's throwaway test database, never your data.
"""

import io
import json
import os
import resource
import statistics
import threading
import time
from unittest import mock

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from tests.conftest import make_user
from tickets.models import Comment, Customer, Ticket

pytestmark = [pytest.mark.stress, pytest.mark.django_db(transaction=True)]

TICKETS = int(os.environ.get("STRESS_TICKETS", "25000"))
P95_BUDGET_MS = float(os.environ.get("STRESS_P95_MS", "1500"))
RUNS = 10
MAX_QUERIES = 20


@pytest.fixture(autouse=True)
def _memory_storage(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "default": {"BACKEND": "tests.test_tickets.MemoryS3Storage"},
    }


def time_page(client: Client, url: str) -> dict:
    """Warm-up once, then RUNS timed requests. Times in ms."""
    client.get(url, secure=True)
    times = []
    for _ in range(RUNS):
        with CaptureQueriesContext(connection) as queries:
            start = time.perf_counter()
            response = client.get(url, secure=True)
            times.append((time.perf_counter() - start) * 1000)
        assert response.status_code == 200, url
    times.sort()
    return {
        "p50": statistics.median(times),
        "p95": times[min(len(times) - 1, round(0.95 * (len(times) - 1)))],
        "max": times[-1],
        "queries": len(queries),
        "kb": len(response.content) / 1024,
    }


def print_table(title: str, rows: dict[str, dict]) -> None:
    print(f"\n{title}\n{'page':<44}{'p50 ms':>9}{'p95 ms':>9}{'max ms':>9}{'queries':>9}{'KB':>8}")
    for label, r in rows.items():
        print(
            f"{label:<44}{r['p50']:>9.0f}{r['p95']:>9.0f}{r['max']:>9.0f}{r['queries']:>9}{r['kb']:>8.0f}"
        )


def test_admin_under_load(lead, agent, settings):
    report: dict[str, object] = {"tickets": TICKETS}

    # 1. Seed.
    start = time.perf_counter()
    call_command("seed_demo", tickets=TICKETS, seed=42, stdout=io.StringIO())
    report["seed_seconds"] = round(time.perf_counter() - start, 1)
    counts = {
        "tickets": Ticket.objects.count(),
        "comments": Comment.objects.count(),
        "customers": Customer.objects.count(),
    }
    with connection.cursor() as cursor:
        # Fresh planner statistics, as autovacuum would leave them; otherwise it starts mid-run.
        cursor.execute("ANALYZE")
        cursor.execute(
            "SELECT relname, pg_total_relation_size(relid) FROM pg_stat_user_tables "
            "WHERE relname LIKE 'tickets_%%' ORDER BY 2 DESC"
        )
        sizes = {name: round(size / 1024 / 1024, 1) for name, size in cursor.fetchall()}
    print(f"\nSeeded {counts} in {report['seed_seconds']} s. Table sizes (MB): {sizes}")

    # 2. Pages, as each role.
    own = Ticket.objects.filter(assignee=agent.agent).first()
    customer = Customer.objects.filter(tickets__isnull=False).first()
    lead_client, agent_client = Client(), Client()
    lead_client.force_login(lead)
    agent_client.force_login(agent)
    pages = {
        "Lead": (
            lead_client,
            {
                "dashboard": "/admin/",
                "tickets (default)": "/admin/tickets/ticket/",
                "tickets: open, breached": "/admin/tickets/ticket/?status__exact=open&sla=breached",
                "tickets: search text": "/admin/tickets/ticket/?q=refund",
                "tickets: search #id": f"/admin/tickets/ticket/?q=%23{own.pk}",
                "tickets: sorted by age": "/admin/tickets/ticket/?o=-8",
                "tickets: last page": f"/admin/tickets/ticket/?p={max(TICKETS // 50, 1)}",
                "ticket change page": f"/admin/tickets/ticket/{own.pk}/change/",
                "customers": "/admin/tickets/customer/",
                "customer change (ticket inline)": f"/admin/tickets/customer/{customer.pk}/change/",
                "agents (open-ticket counts)": "/admin/tickets/agent/",
                "tags (ticket counts)": "/admin/tickets/tag/",
            },
        ),
        "Agent": (
            agent_client,
            {
                "tickets (own + queue)": "/admin/tickets/ticket/",
                "tickets: my tickets": "/admin/tickets/ticket/?queue=mine",
                "ticket change page": f"/admin/tickets/ticket/{own.pk}/change/",
                "customer change (ticket inline)": f"/admin/tickets/customer/{customer.pk}/change/",
            },
        ),
    }
    slow = []
    for role, (client, urls) in pages.items():
        rows = {label: time_page(client, url) for label, url in urls.items()}
        print_table(f"{role} pages ({RUNS} runs each, warm)", rows)
        report[role] = rows
        slow += [
            f"{role} {label}"
            for label, r in rows.items()
            if r["p95"] > P95_BUDGET_MS or r["queries"] > MAX_QUERIES
        ]

    # 3. Bulk action: an agent claims 10 queue tickets in one go (each row takes its own locks).
    queue = list(Ticket.objects.filter(assignee__isnull=True).values_list("pk", flat=True)[:10])
    start = time.perf_counter()
    agent_client.post(
        "/admin/tickets/ticket/",
        {"action": "claim_selected", "_selected_action": queue},
        secure=True,
    )
    report["bulk_claim_10_ms"] = round((time.perf_counter() - start) * 1000)
    print(f"\nBulk claim of {len(queue)} tickets: {report['bulk_claim_10_ms']} ms")

    # 4. Race: 8 agents claim the same ticket at once; exactly one may win.
    target = Ticket.objects.filter(assignee__isnull=True).first()
    racers = [make_user(f"racer{i}", "Agent").agent for i in range(8)]
    barrier, results = threading.Barrier(len(racers)), []

    def claim(racer):
        try:
            barrier.wait()
            Ticket.objects.get(pk=target.pk).claim(racer)
            results.append("won")
        except ValidationError:
            results.append("lost")
        finally:
            connection.close()

    start = time.perf_counter()
    threads = [threading.Thread(target=claim, args=(r,)) for r in racers]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    report["race_ms"] = round((time.perf_counter() - start) * 1000)
    winners = results.count("won")
    print(f"Concurrent claim by {len(racers)} agents: {winners} winner in {report['race_ms']} ms")

    # 5. Form assistant overhead (provider mocked, so this is our own work: building the prompt).
    settings.LLM_BASE_URL, settings.LLM_MODEL, settings.GROQ_API_KEY = "https://llm.test", "m", "k"
    reply = json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode()
    with mock.patch("core.assistant.urlopen", side_effect=lambda *a, **k: io.BytesIO(reply)):
        timings = []
        for _ in range(RUNS):
            start = time.perf_counter()
            lead_client.post(
                "/admin/assistant/",
                {
                    "app_label": "tickets",
                    "model_name": "ticket",
                    "object_id": own.pk,
                    "question": "?",
                },
                content_type="application/json",
                secure=True,
            )
            timings.append((time.perf_counter() - start) * 1000)
    report["assistant_p50_ms"] = round(statistics.median(timings))
    print(f"Form assistant overhead (LLM mocked): p50 {report['assistant_p50_ms']} ms")

    report["peak_rss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    print(f"Peak memory of this process: {report['peak_rss_mb']} MB")

    assert winners == 1
    assert not slow, f"Over budget (p95 > {P95_BUDGET_MS} ms or > {MAX_QUERIES} queries): {slow}"
