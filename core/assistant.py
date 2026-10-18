"""AI form assistant: answers "what does this field mean" from the user's own admin form.

Only form metadata (labels, help text, choices, flags) and the ticket rules are sent, never
ticket or customer data. The form comes from the ModelAdmin for this request, so a field
hidden from a role never reaches the prompt. Any provider problem returns the field's own
help text instead, so the admin never breaks.
"""

import json
import logging
import re
from typing import Any
from urllib.request import Request, urlopen

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.utils import flatten_fieldsets, help_text_for_field, label_for_field
from django.core.exceptions import FieldDoesNotExist, PermissionDenied
from django.http import Http404, HttpRequest, JsonResponse
from django.utils.html import strip_tags
from django.utils.text import capfirst
from django.views.decorators.http import require_POST

from core import ratelimit
from tickets.models import REOPEN_WINDOW, SLA_HOURS, TRANSITIONS, Ticket

logger = logging.getLogger(__name__)

MAX_QUESTION = 500
RATE_LIMIT = 20  # questions per user per hour
TIMEOUT = 8  # seconds
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"\+?\d[\d\s().-]{6,}\d")
SYSTEM = (
    "You help support staff fill in one form in a Django admin. Answer only from the form "
    "description and rules below; if they don't cover the question, say so. Reply in plain "
    "text, no Markdown, at most 120 words. Never invent fields or options."
)


def clean_question(raw: str) -> str:
    """Drop control characters and scrub emails and phone numbers (the caller caps length)."""
    text = "".join(ch for ch in raw if ch.isprintable() or ch == "\n")
    return PHONE.sub("[phone]", EMAIL.sub("[email]", text)).strip()


def describe_form(request: HttpRequest, model_admin: Any, obj: Any) -> list[dict[str, Any]]:
    """Every field this user's change form shows, inlines included. Metadata only."""
    sources = [(model_admin, model_admin.get_form(request, obj))] + [
        (inline, inline.get_formset(request, obj).form)
        for inline in model_admin.get_inline_instances(request, obj)
    ]
    fields = []
    for owner, form in sources:
        readonly = owner.get_readonly_fields(request, obj)
        for name in flatten_fieldsets(owner.get_fieldsets(request, obj)):
            field = form.base_fields.get(name)
            editable = field is not None and name not in readonly
            try:
                # Only static model choices: a foreign key's options would be real records.
                choices = [str(label) for _, label in owner.model._meta.get_field(name).flatchoices]
            except FieldDoesNotExist:
                choices = []
            fields.append(
                {
                    "name": name,
                    "label": capfirst(
                        str(field.label if editable else label_for_field(name, owner.model, owner))
                    ),
                    "help": strip_tags(
                        str(field.help_text if editable else help_text_for_field(name, owner.model))
                    ),
                    "required": editable and field.required,
                    "read_only": not editable,
                    "choices": choices,
                }
            )
    return fields


def field_line(field: dict[str, Any]) -> str:
    flag = (
        "read-only for you"
        if field["read_only"]
        else "required"
        if field["required"]
        else "optional"
    )
    line = f"{field['label']} ({field['name']}), {flag}."
    if field["help"]:
        line += f" {field['help'].rstrip('.')}."
    if field["choices"]:
        line += f" Choices: {', '.join(field['choices'])}."
    return line


def ticket_rules() -> str:
    moves = "; ".join(
        f"{source.label} → {', '.join(s.label for s in Ticket.Status if s in targets)}"
        for source, targets in TRANSITIONS.items()
    )
    sla = ", ".join(f"{priority.label} {hours} h" for priority, hours in SLA_HOURS.items())
    return (
        "Status changes only through the workflow buttons on the page, never by editing. "
        f"Allowed moves: {moves}. New → Open needs an assignee. Resolving needs a public "
        "reply from an agent. Only a support lead can close a ticket or reopen a closed one, "
        f"and only within {REOPEN_WINDOW.days} days of closing. "
        f"First-response SLA by priority: {sla}."
    )


def build_messages(
    model: Any, fields: list[dict[str, Any]], field: dict[str, Any] | None, question: str
) -> list[dict[str, str]]:
    context = f"Form: {model._meta.verbose_name}.\nFields:\n" + "\n".join(
        f"- {field_line(f)}" for f in fields
    )
    if model is Ticket:
        context += f"\nRules: {ticket_rules()}"
    asked = f"About the field: {field['label']} ({field['name']})\n" if field else ""
    return [
        {"role": "system", "content": f"{SYSTEM}\n\n{context}"},
        {"role": "user", "content": asked + question},
    ]


def ask_llm(messages: list[dict[str, str]]) -> str:
    request = Request(  # noqa: S310 (the URL comes from settings, not the user)
        f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(
            {
                "model": settings.LLM_MODEL,
                "messages": messages,
                "max_completion_tokens": 600,
                "reasoning_effort": "low",
            }
        ).encode(),
        headers={
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "ticket-tracker",  # Groq's edge refuses urllib's default agent
        },
    )
    # shortcut: the timeout is per socket read, not total; a slow trickle could run longer.
    with urlopen(request, timeout=TIMEOUT) as response:  # noqa: S310
        return str(json.load(response)["choices"][0]["message"]["content"] or "").strip()


def within_rate_limit(user: Any) -> bool:
    return ratelimit.hit(f"assistant:{user.pk}", 60 * 60) <= RATE_LIMIT


def fallback(field: dict[str, Any] | None, note: str) -> JsonResponse:
    hint = field_line(field) if field else "Click into a field and ask again to see its help."
    return JsonResponse({"answer": f"{note}\n\n{hint}", "source": "fallback"})


@require_POST
def assistant(request: HttpRequest) -> JsonResponse:
    try:
        body = json.loads(request.body)
        model = apps.get_model(body["app_label"], body["model_name"])
        question = str(body["question"])
        object_id = body.get("object_id")
    except (ValueError, LookupError, TypeError, AttributeError):
        return JsonResponse({"error": "Bad request."}, status=400)
    model_admin = admin.site._registry.get(model)
    if model_admin is None:
        raise Http404
    # get_object applies the admin's own visibility (an Agent can't open others' tickets).
    obj = model_admin.get_object(request, str(object_id)) if object_id else None
    if (object_id and obj is None) or not model_admin.has_view_or_change_permission(request, obj):
        raise PermissionDenied
    if len(question) > MAX_QUESTION:
        return JsonResponse({"error": f"Keep it under {MAX_QUESTION} characters."}, status=400)
    question = clean_question(question)
    if not question:
        return JsonResponse({"error": "Type a question first."}, status=400)

    fields = describe_form(request, model_admin, obj)
    field = next((f for f in fields if f["name"] == body.get("field")), None)
    if not (settings.LLM_BASE_URL and settings.LLM_MODEL and settings.GROQ_API_KEY):
        return fallback(
            field, "The AI assistant isn't set up here, so this is the form's own help."
        )
    if not within_rate_limit(request.user):
        return fallback(
            field, f"That's {RATE_LIMIT} questions this hour, so this is the form's own help."
        )
    try:
        answer = ask_llm(build_messages(model, fields, field, question))
    except Exception:  # timeout, 429, bad JSON: the admin must never break on the provider
        logger.warning("Form assistant fell back", exc_info=True)
        answer = ""
    if not answer:
        return fallback(
            field, "The AI assistant couldn't answer just now, so this is the form's own help."
        )
    return JsonResponse({"answer": answer, "source": "ai"})
