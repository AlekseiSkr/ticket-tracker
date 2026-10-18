"""Support admin. Roles are checked by permission; visibility comes from visible_to()."""

from collections import Counter
from collections.abc import Callable
from typing import Any

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, OuterRef, Q, QuerySet, Subquery
from django.db.models.functions import Coalesce
from django.forms import BaseInlineFormSet
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django.utils import formats, timezone
from django.utils.html import format_html
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.contrib.filters.admin import AutocompleteSelectFilter, AutocompleteSelectMultipleFilter
from unfold.decorators import action, display
from unfold.forms import ActionForm

from tickets.models import OPEN_STATUSES, Agent, Comment, Customer, Tag, Ticket

S = Ticket.Status
# Every key must be listed: Unfold shows the raw value for a missing one. "neutral" renders grey.
STATUS_COLORS = {
    S.NEW: "info",
    S.OPEN: "primary",
    S.PENDING_CUSTOMER: "neutral",
    S.RESOLVED: "success",
    S.CLOSED: "neutral",
}
P = Ticket.Priority
PRIORITY_COLORS = {P.URGENT: "danger", P.HIGH: "warning", P.NORMAL: "neutral", P.LOW: "neutral"}


def agent_for(user: Any) -> Agent:
    """Staff who write comments or claim tickets need an Agent profile; create it on first use."""
    return Agent.objects.get_or_create(user=user)[0]


class TicketActionForm(ActionForm):
    agent = forms.ModelChoiceField(
        queryset=Agent.objects.select_related("user"), required=False, label="Agent"
    )
    priority = forms.ChoiceField(
        choices=[("", "Priority")] + Ticket.Priority.choices, required=False, label=""
    )


class SlaBreachedFilter(admin.SimpleListFilter):
    title = "SLA"
    parameter_name = "sla"

    def lookups(self, request: HttpRequest, model_admin: Any) -> list[tuple[str, str]]:
        return [("breached", "Breached"), ("on_track", "On track")]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Any]) -> QuerySet[Any]:
        if self.value():
            return queryset.filter(is_sla_breached=self.value() == "breached")
        return queryset


class QueueFilter(admin.SimpleListFilter):
    title = "Queue"
    parameter_name = "queue"

    def lookups(self, request: HttpRequest, model_admin: Any) -> list[tuple[str, str]]:
        return [("mine", "My tickets"), ("unassigned", "Unassigned")]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Any]) -> QuerySet[Any]:
        if self.value() == "mine":
            return queryset.filter(assignee__user=request.user)
        if self.value() == "unassigned":
            return queryset.filter(assignee__isnull=True)
        return queryset


class CommentFormSet(BaseInlineFormSet):
    request_user: Any = None

    def _construct_form(self, i: int, **kwargs: Any) -> Any:
        form = super()._construct_form(i, **kwargs)  # type: ignore[misc]
        # The current agent writes every new comment. Set it before validation so the
        # "internal notes need an agent" constraint passes; only on a real submit.
        if self.is_bound and form.instance.pk is None:
            form.instance.author = agent_for(self.request_user)
        return form


class CommentInline(StackedInline):
    model = Comment
    formset = CommentFormSet
    extra = 1
    fields = ["body", "is_internal", "attachment", "written_by", "attachment_link", "posted_at"]
    readonly_fields = ["written_by", "attachment_link", "posted_at"]

    def get_formset(self, request: HttpRequest, obj: Any = None, **kwargs: Any) -> Any:
        formset = super().get_formset(request, obj, **kwargs)
        formset.request_user = request.user
        return formset

    def get_queryset(self, request: HttpRequest) -> QuerySet[Comment]:
        return super().get_queryset(request).select_related("author__user")

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False  # comments are a log: add new ones, never edit old ones

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    @display(description="Written by")
    def written_by(self, comment: Comment) -> str:
        if comment.pk is None:
            return "-"
        return (
            f"{comment.author} (internal note)"
            if comment.is_internal
            else str(comment.author or "Customer")
        )

    @display(description="Posted")
    def posted_at(self, comment: Comment) -> str:
        return formats.localize(timezone.localtime(comment.created_at)) if comment.pk else "-"

    @display(description="Attachment")
    def attachment_link(self, comment: Comment) -> str:
        if not comment.attachment:
            return "-"
        return format_html('<a href="{}">Download</a>', reverse("attachment", args=[comment.pk]))


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = [
        "id",
        "subject",
        "customer",
        "assignee",
        "status_badge",
        "priority_badge",
        "sla_badge",
        "age_display",
        "comment_count",
    ]
    list_display_links = ["id", "subject"]
    list_filter = [
        QueueFilter,
        "status",
        "priority",
        SlaBreachedFilter,
        "channel",
        ("assignee", AutocompleteSelectFilter),
        ("tags", AutocompleteSelectMultipleFilter),
    ]
    list_filter_submit = True
    search_fields = ["=id", "subject", "customer__name", "customer__email"]
    search_help_text = "Search by ticket number, subject, or customer name or email."
    date_hierarchy = "created_at"
    list_select_related = ["customer", "assignee__user"]
    list_per_page = 50
    show_full_result_count = False  # skips a second COUNT(*) over 25k rows on every page
    autocomplete_fields = ["customer", "assignee", "tags"]
    inlines = [CommentInline]
    action_form = TicketActionForm
    actions = [
        "claim_selected",
        "resolve_selected",
        "assign_selected",
        "close_selected",
        "priority_selected",
    ]
    actions_detail = [
        "claim_detail",
        "pending_detail",
        "reopen_detail",
        "resolve_detail",
        "close_detail",
    ]
    fieldsets = [
        (None, {"fields": ["subject", "description", "customer", "tags", "channel"]}),
        ("Workflow", {"fields": ["status", "priority", "assignee"]}),
        (
            "SLA",
            {
                "fields": [
                    "sla_due_display",
                    "sla_state",
                    "created_at",
                    "first_response_at",
                    "resolved_at",
                    "closed_at",
                ]
            },
        ),
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Ticket]:
        # A correlated subquery, not Count(): Postgres counts only the rows on the page instead
        # of grouping every ticket with its comments (about 10x faster at 25k tickets).
        comments = Comment.objects.filter(ticket=OuterRef("pk")).order_by().values("ticket")
        num_comments = Subquery(comments.annotate(n=Count("pk")).values("n"))
        qs = Ticket.objects.visible_to(request.user).with_sla()
        return qs.annotate(num_comments=Coalesce(num_comments, 0))

    def get_readonly_fields(self, request: HttpRequest, obj: Any = None) -> list[str]:
        # Status only moves through the workflow buttons and actions.
        fields = [
            "status",
            "sla_due_display",
            "sla_state",
            "created_at",
            "first_response_at",
            "resolved_at",
            "closed_at",
        ]
        if not request.user.has_perm("tickets.change_priority"):
            fields.append("priority")
        if not request.user.has_perm("tickets.assign_ticket"):
            fields.append("assignee")
        return fields

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        actions = super().get_actions(request)
        for name, perm in [
            ("assign_selected", "assign_ticket"),
            ("close_selected", "close_ticket"),
            ("priority_selected", "change_priority"),
        ]:
            if not request.user.has_perm(f"tickets.{perm}"):
                actions.pop(name, None)
        return actions

    def get_search_results(
        self, request: HttpRequest, queryset: QuerySet[Any], search_term: str
    ) -> Any:
        # "#123" finds ticket 123 too.
        return super().get_search_results(request, queryset, search_term.lstrip("#"))

    # --- Columns ---------------------------------------------------------------------------

    @display(description="Status", ordering="status", label=STATUS_COLORS)
    def status_badge(self, ticket: Ticket) -> Any:
        return ticket.status, ticket.get_status_display()

    @display(description="Priority", ordering="priority", label=PRIORITY_COLORS)
    def priority_badge(self, ticket: Ticket) -> Any:
        return ticket.priority, ticket.get_priority_display()

    @display(
        description="SLA", ordering="is_sla_breached", label={True: "danger", False: "success"}
    )
    def sla_badge(self, ticket: Any) -> Any:
        return ticket.is_sla_breached, "Breached" if ticket.is_sla_breached else "On track"

    @display(description="SLA")
    def sla_state(self, ticket: Any) -> str:
        return "Breached" if ticket.is_sla_breached else "On track"

    @display(description="First response due", ordering="sla_due_at")
    def sla_due_display(self, ticket: Any) -> str:
        return formats.localize(timezone.localtime(ticket.sla_due_at))

    @display(description="Age", ordering="age")
    def age_display(self, ticket: Any) -> str:
        days, hours = ticket.age.days, ticket.age.seconds // 3600
        return f"{days}d {hours}h" if days else f"{hours}h"

    @display(description="Comments", ordering="num_comments")
    def comment_count(self, ticket: Any) -> int:
        return int(ticket.num_comments)

    # --- Bulk actions: each loops over the model's own rules ------------------------------

    def _bulk(
        self,
        request: HttpRequest,
        queryset: QuerySet[Ticket],
        verb: str,
        apply: Callable[[Ticket], None],
    ) -> None:
        done, skipped = 0, Counter[str]()
        for ticket in queryset.select_related("assignee"):
            try:
                apply(ticket)
                done += 1
            except (ValidationError, PermissionDenied) as exc:
                reason = exc.messages[0] if isinstance(exc, ValidationError) else str(exc)
                skipped[reason] += 1
        reasons = "; ".join(f"{n} × {reason}" for reason, n in skipped.items())
        level = messages.WARNING if skipped else messages.SUCCESS
        self.message_user(
            request,
            f"{done} {verb}, {sum(skipped.values())} skipped"
            + (f" ({reasons})" if reasons else "."),
            level,
        )

    def _form_value(self, request: HttpRequest, field: str) -> Any:
        form = TicketActionForm(request.POST)
        form.fields["action"].choices = self.get_action_choices(request)
        return form.cleaned_data.get(field) if form.is_valid() else None

    @admin.action(description="Claim selected tickets")
    def claim_selected(self, request: HttpRequest, queryset: QuerySet[Ticket]) -> None:
        agent = agent_for(request.user)
        self._bulk(request, queryset, "claimed", lambda t: t.claim(agent))

    @admin.action(description="Resolve selected tickets")
    def resolve_selected(self, request: HttpRequest, queryset: QuerySet[Ticket]) -> None:
        self._bulk(
            request, queryset, "resolved", lambda t: t.transition_to(S.RESOLVED, request.user)
        )

    @admin.action(description="Assign selected to the chosen agent")
    def assign_selected(self, request: HttpRequest, queryset: QuerySet[Ticket]) -> None:
        agent = self._form_value(request, "agent")
        if agent is None:
            self.message_user(
                request, "Pick an agent in the Agent box, then run the action.", messages.ERROR
            )
            return
        self._bulk(request, queryset, "assigned", lambda t: t.assign(agent, request.user))

    @admin.action(description="Close selected resolved tickets")
    def close_selected(self, request: HttpRequest, queryset: QuerySet[Ticket]) -> None:
        self._bulk(request, queryset, "closed", lambda t: t.transition_to(S.CLOSED, request.user))

    @admin.action(description="Set the chosen priority on selected")
    def priority_selected(self, request: HttpRequest, queryset: QuerySet[Ticket]) -> None:
        priority = self._form_value(request, "priority")
        if not priority:
            self.message_user(
                request, "Pick a priority in the Priority box, then run the action.", messages.ERROR
            )
            return
        self._bulk(request, queryset, "updated", lambda t: t.set_priority(priority, request.user))

    # --- Workflow buttons on the ticket page -----------------------------------------------

    def has_close_ticket_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        # A method, not "tickets.close_ticket": Unfold checks dotted permissions with a DB query
        # at startup, which fails on a fresh database (CI's makemigrations --check).
        return bool(request.user.has_perm("tickets.close_ticket"))

    def _detail(
        self, request: HttpRequest, object_id: str, apply: Callable[[Ticket], None], done: str
    ) -> HttpResponseRedirect:
        ticket = self.get_object(request, object_id)
        if ticket is None:
            raise PermissionDenied  # not visible to this user
        try:
            apply(ticket)
            self.message_user(request, done, messages.SUCCESS)
        except ValidationError as exc:
            self.message_user(request, exc.messages[0], messages.ERROR)
        except PermissionDenied as exc:
            self.message_user(request, str(exc), messages.ERROR)
        return HttpResponseRedirect(reverse("admin:tickets_ticket_change", args=[object_id]))

    @action(description="Claim", url_path="claim", icon="front_hand")
    def claim_detail(self, request: HttpRequest, object_id: str) -> HttpResponseRedirect:
        agent = agent_for(request.user)
        return self._detail(
            request, object_id, lambda t: t.claim(agent), "You claimed this ticket."
        )

    @action(description="Waiting on customer", url_path="pending", icon="hourglass_top")
    def pending_detail(self, request: HttpRequest, object_id: str) -> HttpResponseRedirect:
        return self._detail(
            request,
            object_id,
            lambda t: t.transition_to(S.PENDING_CUSTOMER, request.user),
            "Marked as waiting on the customer.",
        )

    @action(description="Open", url_path="open", icon="play_arrow")
    def reopen_detail(self, request: HttpRequest, object_id: str) -> HttpResponseRedirect:
        return self._detail(
            request, object_id, lambda t: t.transition_to(S.OPEN, request.user), "Ticket is open."
        )

    @action(description="Resolve", url_path="resolve", icon="task_alt")
    def resolve_detail(self, request: HttpRequest, object_id: str) -> HttpResponseRedirect:
        return self._detail(
            request,
            object_id,
            lambda t: t.transition_to(S.RESOLVED, request.user),
            "Ticket resolved.",
        )

    @action(description="Close", url_path="close", icon="lock", permissions=["close_ticket"])
    def close_detail(self, request: HttpRequest, object_id: str) -> HttpResponseRedirect:
        return self._detail(
            request, object_id, lambda t: t.transition_to(S.CLOSED, request.user), "Ticket closed."
        )


class TicketInline(TabularInline):
    """Read-only list of a customer's tickets, limited to what this user may see."""

    model = Ticket
    fields = ["subject", "status", "priority", "assignee", "created_at"]
    readonly_fields = fields
    show_change_link = True
    per_page = 10
    extra = 0

    def get_queryset(self, request: HttpRequest) -> QuerySet[Ticket]:
        return Ticket.objects.visible_to(request.user).select_related("assignee__user")

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ["name", "email", "company", "country", "created_at"]
    list_filter = ["country"]
    search_fields = ["name", "email", "company"]
    show_full_result_count = False
    inlines = [TicketInline]


@admin.register(Agent)
class AgentAdmin(ModelAdmin):
    list_display = ["__str__", "team", "open_tickets", "max_open_tickets"]
    list_filter = ["team"]
    search_fields = ["user__username", "user__first_name", "user__last_name"]
    autocomplete_fields = ["user"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Agent]:
        open_q = Q(tickets__status__in=OPEN_STATUSES)
        return (
            super()
            .get_queryset(request)
            .select_related("user")
            .annotate(num_open=Count("tickets", filter=open_q))
        )

    @display(description="Open tickets", ordering="num_open")
    def open_tickets(self, agent: Any) -> int:
        return int(agent.num_open)


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ["name", "ticket_count"]
    search_fields = ["name"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Tag]:
        return super().get_queryset(request).annotate(num_tickets=Count("tickets"))

    @display(description="Tickets", ordering="num_tickets")
    def ticket_count(self, tag: Any) -> int:
        return int(tag.num_tickets)
