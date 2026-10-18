import io
import json
from email.message import Message
from unittest import mock
from urllib.error import HTTPError

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client

from core.assistant import RATE_LIMIT, clean_question
from tests.conftest import make_user
from tests.test_tickets import ticket_for

URL = "/admin/assistant/"


@pytest.fixture(autouse=True)
def _llm(settings):
    settings.LLM_BASE_URL = "https://llm.example/v1"
    settings.LLM_MODEL = "test-model"
    settings.GROQ_API_KEY = "test-key"
    cache.clear()


def reply_with(text):
    return io.BytesIO(json.dumps({"choices": [{"message": {"content": text}}]}).encode())


def ask(client, question="What does this mean?", model="ticket", **extra):
    payload = {"app_label": "tickets", "model_name": model, "question": question, **extra}
    return client.post(URL, json.dumps(payload), content_type="application/json", secure=True)


def sent_prompt(urlopen):
    request = urlopen.call_args.args[0]
    assert request.headers["Authorization"] == "Bearer test-key"
    return "\n".join(m["content"] for m in json.loads(request.data)["messages"])


def test_prompt_has_form_metadata_and_rules_but_no_ticket_data(client, customer, lead):
    ticket = ticket_for(customer, subject="Secret outage at ACME")
    client.force_login(lead)
    with mock.patch("core.assistant.urlopen", return_value=reply_with("Use High.")) as urlopen:
        response = ask(client, object_id=ticket.pk, field="priority")
    assert response.json() == {"answer": "Use High.", "source": "ai"}
    prompt = sent_prompt(urlopen)
    assert "About the field: Priority (priority)" in prompt
    assert "Choices: Low, Normal, High, Urgent." in prompt
    assert "Internal notes are visible to agents only" in prompt  # the comment inline
    assert "Urgent 1 h" in prompt and "New → Open" in prompt
    for data in ("Secret outage", "anna@customer.example", "Anna Saar"):
        assert data not in prompt


def test_agent_prompt_marks_lead_only_fields_read_only(client, customer, agent):
    ticket = ticket_for(customer, agent.agent, status="open")
    client.force_login(agent)
    with mock.patch("core.assistant.urlopen", return_value=reply_with("Ask a lead.")) as urlopen:
        ask(client, object_id=ticket.pk)
    prompt = sent_prompt(urlopen)
    assert "Priority (priority), read-only for you." in prompt
    assert "Assignee (assignee), read-only for you." in prompt
    assert "Subject (subject), required." in prompt


def test_agent_never_gets_a_prompt_for_lead_only_forms(client, agent):
    client.force_login(agent)
    with mock.patch("core.assistant.urlopen") as urlopen:
        assert ask(client, model="agent", field="max_open_tickets").status_code == 403
    urlopen.assert_not_called()


def test_agent_cannot_ask_about_another_agents_ticket(client, customer, agent):
    theirs = ticket_for(customer, make_user("kati", "Agent").agent, status="open")
    client.force_login(agent)
    assert ask(client, object_id=theirs.pk).status_code == 403


_ERRORS = [TimeoutError(), HTTPError(URL, 429, "Too Many", Message(), None)]


@pytest.mark.parametrize("error", _ERRORS)
def test_provider_failure_falls_back_to_help_text(client, lead, error):
    client.force_login(lead)
    with mock.patch("core.assistant.urlopen", side_effect=error):
        response = ask(client, model="agent", field="max_open_tickets")
    assert response.status_code == 200
    assert response.json()["source"] == "fallback"
    assert "Work-in-progress cap" in response.json()["answer"]


def test_missing_config_falls_back_without_calling(client, lead, settings):
    settings.GROQ_API_KEY = ""
    client.force_login(lead)
    with mock.patch("core.assistant.urlopen") as urlopen:
        response = ask(client)
    urlopen.assert_not_called()
    assert response.json()["source"] == "fallback"
    assert "Click into a field" in response.json()["answer"]


def test_question_is_scrubbed_and_capped(client, lead):
    question = "Mail anna@customer.example or call +372 5555 1234\x00\x1b?"
    assert clean_question(question) == "Mail [email] or call [phone]?"
    client.force_login(lead)
    assert ask(client, "x" * 501).status_code == 400
    assert ask(client, "\x00 ").status_code == 400
    assert ask(client, model="nope").status_code == 400


def test_rate_limit_per_user(client, lead):
    client.force_login(lead)
    with mock.patch("core.assistant.urlopen", side_effect=lambda *a, **k: reply_with("ok")):
        sources = [ask(client).json()["source"] for _ in range(RATE_LIMIT + 1)]
    assert sources == ["ai"] * RATE_LIMIT + ["fallback"]


def test_staff_only_and_csrf_protected(client, lead):
    User.objects.create_user("outsider", password="x")
    client.login(username="outsider", password="x")
    assert ask(client).status_code == 302  # to the admin login
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(lead)
    assert ask(strict).status_code == 403
    assert client.get(URL, secure=True).status_code != 200


def test_widget_is_on_every_change_form(client, customer, lead):
    client.force_login(lead)
    for page in (f"/admin/tickets/customer/{customer.pk}/change/", "/admin/tickets/ticket/add/"):
        html = client.get(page, secure=True).content.decode()
        assert 'class="assistant"' in html and "core/assistant.js" in html, page


def test_field_list_offers_read_only_dropdown_and_inline_fields(client, customer, agent):
    ticket = ticket_for(customer, agent.agent, status="open")
    client.force_login(agent)
    html = client.get(f"/admin/tickets/ticket/{ticket.pk}/change/", secure=True).content.decode()
    start = html.index('id="assistant-field"')
    picker = html[start : html.index("</select>", start)]
    for name in ("status", "priority", "customer", "tags", "body"):  # read-only, dropdowns, inline
        assert f'value="{name}"' in picker, name
