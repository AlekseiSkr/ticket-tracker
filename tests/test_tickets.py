import threading
from datetime import timedelta

import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import InMemoryStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import connection
from django.db.models import Min, Q
from django.utils import timezone

from tickets.models import OPEN_STATUSES, Agent, Comment, Customer, Ticket
from tickets.validators import MAX_ATTACHMENT_BYTES, validate_attachment

S = Ticket.Status
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 32


class MemoryS3Storage(InMemoryStorage):
    """In-memory storage that takes the S3 backend's url(parameters=...) argument."""

    def url(self, name, parameters=None, expire=None, http_method=None):
        return super().url(name)


@pytest.fixture(autouse=True)
def _memory_storage(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "default": {"BACKEND": "tests.test_tickets.MemoryS3Storage"},
    }


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


def ticket_for(customer, assignee=None, subject="Can't log in", **kwargs):
    return Ticket.objects.create(
        customer=customer, assignee=assignee, subject=subject, description="Help", **kwargs
    )


def reply(ticket, user, internal=False):
    return Comment.objects.create(
        ticket=ticket, author=user.agent, body="On it", is_internal=internal
    )


# --- Workflow rules ------------------------------------------------------------------------


def test_new_ticket_needs_an_assignee_before_opening(customer, lead):
    ticket = ticket_for(customer)
    with pytest.raises(ValidationError, match="Assign"):
        ticket.transition_to(S.OPEN, lead)


def test_illegal_jump_is_rejected(customer, agent):
    ticket = ticket_for(customer, agent.agent)
    with pytest.raises(ValidationError, match="can't move"):
        ticket.transition_to(S.CLOSED, agent)


def test_resolve_needs_a_public_agent_reply(customer, agent):
    ticket = ticket_for(customer, agent.agent, status=S.OPEN)
    reply(ticket, agent, internal=True)
    Comment.objects.create(ticket=ticket, body="Customer follow-up")
    with pytest.raises(ValidationError, match="Reply"):
        ticket.transition_to(S.RESOLVED, agent)
    reply(ticket, agent)
    ticket.transition_to(S.RESOLVED, agent)
    ticket.refresh_from_db()
    assert ticket.status == S.RESOLVED and ticket.resolved_at is not None


def test_only_a_lead_closes_and_reopens_closed_within_14_days(customer, agent, lead):
    ticket = ticket_for(customer, agent.agent, status=S.OPEN)
    reply(ticket, agent)
    ticket.transition_to(S.RESOLVED, agent)
    with pytest.raises(PermissionDenied):
        ticket.transition_to(S.CLOSED, agent)
    ticket.transition_to(S.CLOSED, lead)
    with pytest.raises(PermissionDenied):
        ticket.transition_to(S.OPEN, agent)
    long_ago = timezone.now() - timedelta(days=15)
    Ticket.objects.filter(pk=ticket.pk).update(resolved_at=long_ago, closed_at=long_ago)
    with pytest.raises(ValidationError, match="14 days"):
        ticket.transition_to(S.OPEN, lead)


def test_agent_cannot_move_another_agents_ticket(customer, agent, other_agent):
    ticket = ticket_for(customer, other_agent.agent, status=S.OPEN)
    with pytest.raises(PermissionDenied):
        ticket.transition_to(S.PENDING_CUSTOMER, agent)


def test_first_public_agent_reply_stamps_first_response(customer, agent):
    ticket = ticket_for(customer, agent.agent, status=S.OPEN)
    Comment.objects.create(ticket=ticket, body="Customer again")
    reply(ticket, agent, internal=True)
    ticket.refresh_from_db()
    assert ticket.first_response_at is None
    first = reply(ticket, agent)
    reply(ticket, agent)
    ticket.refresh_from_db()
    assert ticket.first_response_at == first.created_at


def test_sla_annotation_flags_overdue_unanswered_tickets(customer):
    late = ticket_for(
        customer, priority=Ticket.Priority.URGENT, created_at=timezone.now() - timedelta(hours=2)
    )
    fresh = ticket_for(customer, priority=Ticket.Priority.LOW)
    flags = dict(Ticket.objects.with_sla().values_list("pk", "is_sla_breached"))
    assert flags == {late.pk: True, fresh.pk: False}


# --- Claim: work-in-progress cap and concurrency -------------------------------------------


def test_claim_respects_the_cap_and_opens_the_ticket(customer, agent):
    agent.agent.max_open_tickets = 1
    agent.agent.save()
    first, second = ticket_for(customer), ticket_for(customer)
    first.claim(agent.agent)
    first.refresh_from_db()
    assert (first.assignee_id, first.status) == (agent.agent.pk, S.OPEN)
    with pytest.raises(ValidationError, match="cap 1"):
        second.claim(agent.agent)


@pytest.mark.django_db(transaction=True)
def test_concurrent_claims_have_exactly_one_winner(customer, agent, other_agent):
    ticket = ticket_for(customer)
    barrier = threading.Barrier(2)
    results: list[str] = []

    def claim(user):
        try:
            barrier.wait()
            Ticket.objects.get(pk=ticket.pk).claim(user.agent)
            results.append("won")
        except ValidationError:
            results.append("lost")
        finally:
            connection.close()

    threads = [threading.Thread(target=claim, args=(u,)) for u in (agent, other_agent)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["lost", "won"]


# --- Roles and isolation (the leak sweep) --------------------------------------------------


def test_agent_sees_only_own_and_unassigned_tickets(client, customer, agent, other_agent):
    mine = ticket_for(customer, agent.agent, status=S.OPEN, subject="Mine")
    queue = ticket_for(customer, subject="Queue")
    theirs = ticket_for(customer, other_agent.agent, status=S.OPEN, subject="Theirs secret")
    client.force_login(agent)

    listing = client.get("/admin/tickets/ticket/", secure=True).content.decode()
    assert f"/admin/tickets/ticket/{mine.pk}/change/" in listing
    assert f"/admin/tickets/ticket/{queue.pk}/change/" in listing
    assert "Theirs secret" not in listing

    change = client.get(f"/admin/tickets/ticket/{theirs.pk}/change/", secure=True)
    assert change.status_code != 200
    customer_page = client.get(f"/admin/tickets/customer/{customer.pk}/change/", secure=True)
    assert "Theirs secret" not in customer_page.content.decode()

    hidden = Comment.objects.create(
        ticket=theirs, body="logs", attachment=SimpleUploadedFile("a.png", PNG)
    )
    assert client.get(f"/attachments/{hidden.pk}/", secure=True).status_code == 404


def test_agent_attachment_downloads_are_presigned_redirects(client, customer, agent):
    ticket = ticket_for(customer, agent.agent, status=S.OPEN)
    comment = Comment.objects.create(
        ticket=ticket, body="logs", attachment=SimpleUploadedFile("a.png", PNG)
    )
    client.force_login(agent)
    assert client.get(f"/attachments/{comment.pk}/", secure=True).status_code == 302


def test_agent_lacks_lead_actions_pages_and_fields(client, customer, agent):
    ticket = ticket_for(customer, agent.agent, status=S.OPEN)
    client.force_login(agent)
    listing = client.get("/admin/tickets/ticket/", secure=True).content.decode()
    assert 'value="claim_selected"' in listing
    for lead_only in ("assign_selected", "close_selected", "priority_selected", "delete_selected"):
        assert f'value="{lead_only}"' not in listing
    for page in ("/admin/tickets/agent/", "/admin/auth/user/", "/admin/auth/group/"):
        assert client.get(page, secure=True).status_code == 403
    form = client.get(f"/admin/tickets/ticket/{ticket.pk}/change/", secure=True).content.decode()
    assert (
        'name="priority"' not in form
        and 'name="assignee"' not in form
        and 'name="status"' not in form
    )
    assert f"/{ticket.pk}/close/" not in form  # the Close workflow button is lead-only


def test_lead_sees_lead_actions(client, customer, lead):
    ticket = ticket_for(customer)
    client.force_login(lead)
    listing = client.get("/admin/tickets/ticket/", secure=True).content.decode()
    for action in ("assign_selected", "close_selected", "priority_selected"):
        assert f'value="{action}"' in listing
    form = client.get(f"/admin/tickets/ticket/{ticket.pk}/change/", secure=True).content.decode()
    assert f"/{ticket.pk}/close/" in form


def test_agent_writes_an_internal_note_through_the_form(client, customer, agent):
    ticket = ticket_for(customer, agent.agent, status=S.OPEN)
    client.force_login(agent)
    data = {
        "subject": ticket.subject,
        "description": ticket.description,
        "customer": customer.pk,
        "channel": ticket.channel,
        "comments-TOTAL_FORMS": "1",
        "comments-INITIAL_FORMS": "0",
        "comments-MIN_NUM_FORMS": "0",
        "comments-MAX_NUM_FORMS": "1000",
        "comments-0-body": "Escalated to tier 2.",
        "comments-0-is_internal": "on",
    }
    response = client.post(f"/admin/tickets/ticket/{ticket.pk}/change/", data, secure=True)
    assert response.status_code == 302, response.content.decode()[:2000]
    note = ticket.comments.get()
    assert note.is_internal and note.author == agent.agent


def test_bulk_claim_reports_skips(client, customer, agent):
    agent.agent.max_open_tickets = 1
    agent.agent.save()
    tickets = [ticket_for(customer), ticket_for(customer)]
    client.force_login(agent)
    response = client.post(
        "/admin/tickets/ticket/",
        {"action": "claim_selected", "_selected_action": [t.pk for t in tickets]},
        secure=True,
        follow=True,
    )
    assert "1 claimed, 1 skipped" in response.content.decode()
    assert Ticket.objects.filter(assignee=agent.agent).count() == 1


# --- Uploads -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "data", "ok"),
    [
        ("shot.png", PNG, True),
        ("scan.pdf", b"%PDF-1.7 ...", True),
        ("log.txt", "naïve café ✓".encode(), True),
        ("photo.jpg", b"\x89PNG\r\n\x1a\n", False),  # wrong magic bytes for the extension
        ("log.txt", b"MZ\0\0binary", False),
        ("tool.exe", b"MZ", False),
    ],
)
def test_attachment_validation(name, data, ok):
    upload = SimpleUploadedFile(name, data)
    if ok:
        validate_attachment(upload)
    else:
        with pytest.raises(ValidationError):
            validate_attachment(upload)


def test_attachment_size_cap():
    upload = SimpleUploadedFile("big.txt", b"a" * (MAX_ATTACHMENT_BYTES + 1))
    with pytest.raises(ValidationError, match="10 MB"):
        validate_attachment(upload)


# --- Seed ----------------------------------------------------------------------------------


def test_seed_users_needs_passwords_from_env(db, monkeypatch):
    from django.core.exceptions import ImproperlyConfigured

    monkeypatch.delenv("DEMO_LEAD_PASSWORD", raising=False)
    with pytest.raises(ImproperlyConfigured):
        call_command("seed_users")
    monkeypatch.setenv("DEMO_LEAD_PASSWORD", "Lead-demo-2026!x")
    monkeypatch.setenv("DEMO_AGENT_PASSWORD", "Agent-demo-2026!x")
    call_command("seed_users")
    assert User.objects.get(username="lead").has_perm("tickets.close_ticket")
    assert not User.objects.get(username="agent").has_perm("tickets.close_ticket")


def test_seed_demo_obeys_the_workflow_rules(db):
    call_command("seed_demo", tickets=400, seed=7)
    tickets = Ticket.objects.all()
    assert tickets.count() == 400
    public_agent = Q(comments__author__isnull=False, comments__is_internal=False)
    first_replies = tickets.annotate(first=Min("comments__created_at", filter=public_agent))
    for t in first_replies:
        assert t.first_response_at == t.first, t.pk  # stamped by the earliest public agent reply
        if t.status in (S.RESOLVED, S.CLOSED):
            assert t.first is not None
        if t.status == S.NEW:
            assert t.assignee_id is None
    for agent in Agent.objects.all():
        assert agent.tickets.filter(status__in=OPEN_STATUSES).count() < agent.max_open_tickets
    call_command("seed_demo", reset=True, tickets=50, seed=7)  # reset replaces, no duplicates
    assert Ticket.objects.count() == 50


def test_changelist_query_budget(client, db, lead, django_assert_max_num_queries):
    call_command("seed_demo", tickets=300, seed=1)
    client.force_login(lead)
    with django_assert_max_num_queries(15):
        assert client.get("/admin/tickets/ticket/", secure=True).status_code == 200
