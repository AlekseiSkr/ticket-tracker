"""The support domain. Business rules live here; the admin, seed and tests all call them."""

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.db.models import Case, ExpressionWrapper, F, Q, Value, When
from django.db.models.functions import Lower, Now
from django.utils import timezone

from tickets.validators import attachment_upload_to, validate_attachment

# request.user: the stubs type it without has_perm, so rules accept any user-like object.
type AnyUser = Any


class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    company = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=2, blank=True, help_text="ISO 3166-1 alpha-2, e.g. EE.")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"


class Agent(models.Model):
    class Team(models.TextChoices):
        TIER_1 = "tier_1", "Tier 1"
        TIER_2 = "tier_2", "Tier 2"
        BILLING = "billing", "Billing"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent"
    )
    team = models.CharField(max_length=20, choices=Team.choices, default=Team.TIER_1)
    max_open_tickets = models.PositiveIntegerField(
        default=15, help_text="Work-in-progress cap: claims fail once this many tickets are open."
    )

    class Meta:
        ordering = ["user__first_name", "user__username"]
        constraints = [
            models.CheckConstraint(
                condition=Q(max_open_tickets__gt=0), name="agent_wip_cap_positive"
            ),
        ]

    def __str__(self) -> str:
        return self.user.get_full_name() or self.user.get_username()

    @classmethod
    def for_user(cls, user: Any) -> "Agent":
        """Staff who write comments or claim tickets need a profile; create it on first use."""
        return cls.objects.get_or_create(user=user)[0]


class Tag(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(Lower("name"), name="tag_name_ci_unique")]

    def __str__(self) -> str:
        return self.name


class TicketQuerySet(models.QuerySet["Ticket"]):
    def visible_to(self, user: AnyUser) -> "TicketQuerySet":
        """The one visibility rule: Agents see their own tickets plus the unassigned queue."""
        if user.has_perm("tickets.view_all_tickets"):
            return self
        return self.filter(Q(assignee__user_id=user.pk) | Q(assignee__isnull=True))

    def with_sla(self) -> "TicketQuerySet":
        """Annotate sla_due_at, is_sla_breached and age, so they stay sortable in lists."""
        due = Case(
            *[
                When(priority=priority, then=F("created_at") + Value(timedelta(hours=hours)))
                for priority, hours in SLA_HOURS.items()
            ],
            output_field=models.DateTimeField(),
        )
        return self.annotate(sla_due_at=due).annotate(
            is_sla_breached=Case(
                When(
                    Q(first_response_at__gt=F("sla_due_at"))
                    | Q(first_response_at__isnull=True, sla_due_at__lt=Now()),
                    then=Value(True),
                ),
                default=Value(False),
                output_field=models.BooleanField(),
            ),
            age=ExpressionWrapper(Now() - F("created_at"), output_field=models.DurationField()),
        )


class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        OPEN = "open", "Open"
        PENDING_CUSTOMER = "pending_customer", "Pending customer"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        CHAT = "chat", "Chat"
        PHONE = "phone", "Phone"
        WEB = "web", "Web form"

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="tickets")
    assignee = models.ForeignKey(
        Agent, on_delete=models.PROTECT, null=True, blank=True, related_name="tickets"
    )
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.EMAIL)
    tags = models.ManyToManyField(Tag, blank=True, related_name="tickets")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    objects = TicketQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["assignee", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(resolved_at__isnull=True) | Q(status__in=["resolved", "closed"]),
                name="ticket_resolved_at_only_when_resolved",
            ),
            models.CheckConstraint(
                condition=Q(closed_at__isnull=True)
                | Q(resolved_at__isnull=False, closed_at__gte=F("resolved_at")),
                name="ticket_closed_after_resolved",
            ),
            models.CheckConstraint(
                condition=Q(first_response_at__isnull=True)
                | Q(first_response_at__gte=F("created_at")),
                name="ticket_first_response_after_created",
            ),
        ]
        permissions = [
            ("view_all_tickets", "Can see every ticket, not just their own and the queue"),
            ("assign_ticket", "Can assign tickets to any agent"),
            ("close_ticket", "Can close tickets and reopen closed ones"),
            ("change_priority", "Can change ticket priority"),
        ]

    def __str__(self) -> str:
        return f"#{self.pk} {self.subject}"

    # --- Rules -----------------------------------------------------------------------------

    def transition_to(self, new_status: str, by: AnyUser) -> None:
        """Move through the workflow. Raises ValidationError or PermissionDenied."""
        S = Ticket.Status
        with transaction.atomic():
            ticket = Ticket.objects.select_for_update().get(pk=self.pk)
            current, target = S(ticket.status), S(new_status)
            if target not in TRANSITIONS[current]:
                raise ValidationError(
                    f"A {current.label.lower()} ticket can't move to {target.label.lower()}."
                )
            ticket._check_owner(by)
            if target == S.OPEN and current == S.NEW and ticket.assignee_id is None:
                raise ValidationError("Assign the ticket before opening it.")
            if (
                target == S.RESOLVED
                and not ticket.comments.filter(author__isnull=False, is_internal=False).exists()
            ):
                raise ValidationError("Reply to the customer before resolving the ticket.")
            if S.CLOSED in (target, current) and not by.has_perm("tickets.close_ticket"):
                raise PermissionDenied("Only a support lead can close or reopen closed tickets.")
            if (
                current == S.CLOSED
                and ticket.closed_at
                and timezone.now() - ticket.closed_at > REOPEN_WINDOW
            ):
                raise ValidationError("Closed tickets can only be reopened within 14 days.")

            now = timezone.now()
            if target == S.RESOLVED:
                ticket.resolved_at = now
            elif target == S.CLOSED:
                ticket.closed_at = now
            elif target == S.OPEN and current in (S.RESOLVED, S.CLOSED):
                ticket.resolved_at = ticket.closed_at = None
            ticket.status = target
            ticket.save(update_fields=["status", "resolved_at", "closed_at", "updated_at"])
        self._copy_from(ticket)

    def claim(self, agent: Agent) -> None:
        """Take an unassigned ticket. Concurrent claims of one ticket: exactly one wins."""
        self._assign(agent, require_unassigned=True)

    def assign(self, agent: Agent, by: AnyUser) -> None:
        if not by.has_perm("tickets.assign_ticket"):
            raise PermissionDenied("Only a support lead can assign tickets to someone else.")
        self._assign(agent, require_unassigned=False)

    def set_priority(self, priority: str, by: AnyUser) -> None:
        if not by.has_perm("tickets.change_priority"):
            raise PermissionDenied("Only a support lead can change priority.")
        self.priority = Ticket.Priority(priority)
        self.save(update_fields=["priority", "updated_at"])

    def _assign(self, agent: Agent, require_unassigned: bool) -> None:
        with transaction.atomic():
            # Lock order is always ticket then agent, so concurrent claims can't deadlock.
            ticket = Ticket.objects.select_for_update().get(pk=self.pk)
            locked_agent = Agent.objects.select_for_update().get(pk=agent.pk)
            if ticket.status in (Ticket.Status.RESOLVED, Ticket.Status.CLOSED):
                raise ValidationError("Resolved and closed tickets can't be reassigned.")
            if require_unassigned and ticket.assignee_id is not None:
                raise ValidationError("Someone already claimed this ticket.")
            if ticket.assignee_id == locked_agent.pk:
                return
            open_count = locked_agent.tickets.filter(status__in=OPEN_STATUSES).count()
            if open_count >= locked_agent.max_open_tickets:
                cap = locked_agent.max_open_tickets
                raise ValidationError(
                    f"{locked_agent} already has {open_count} open tickets (cap {cap})."
                )
            ticket.assignee = locked_agent
            if ticket.status == Ticket.Status.NEW:
                ticket.status = Ticket.Status.OPEN
            ticket.save(update_fields=["assignee", "status", "updated_at"])
        self._copy_from(ticket)

    def _check_owner(self, by: AnyUser) -> None:
        if (
            self.assignee is not None
            and self.assignee.user_id != by.pk
            and not by.has_perm("tickets.view_all_tickets")
        ):
            raise PermissionDenied("This ticket belongs to another agent.")

    def _copy_from(self, other: "Ticket") -> None:
        for field in ("status", "assignee_id", "resolved_at", "closed_at", "updated_at"):
            setattr(self, field, getattr(other, field))


SLA_HOURS = {
    Ticket.Priority.URGENT: 1,
    Ticket.Priority.HIGH: 4,
    Ticket.Priority.NORMAL: 24,
    Ticket.Priority.LOW: 72,
}
OPEN_STATUSES = [Ticket.Status.NEW, Ticket.Status.OPEN, Ticket.Status.PENDING_CUSTOMER]
REOPEN_WINDOW = timedelta(days=14)
TRANSITIONS: dict[Ticket.Status, set[Ticket.Status]] = {
    Ticket.Status.NEW: {Ticket.Status.OPEN},
    Ticket.Status.OPEN: {Ticket.Status.PENDING_CUSTOMER, Ticket.Status.RESOLVED},
    Ticket.Status.PENDING_CUSTOMER: {Ticket.Status.OPEN, Ticket.Status.RESOLVED},
    Ticket.Status.RESOLVED: {Ticket.Status.OPEN, Ticket.Status.CLOSED},
    Ticket.Status.CLOSED: {Ticket.Status.OPEN},
}


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        Agent,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="comments",
        help_text="Empty means the customer wrote it.",
    )
    body = models.TextField()
    is_internal = models.BooleanField(
        default=False, help_text="Internal notes are visible to agents only, never to the customer."
    )
    attachment = models.FileField(
        upload_to=attachment_upload_to,
        blank=True,
        validators=[validate_attachment],
        help_text="PNG, JPG, PDF or TXT, up to 10 MB.",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(is_internal=False) | Q(author__isnull=False),
                name="comment_internal_needs_agent",
            ),
        ]

    def __str__(self) -> str:
        return f"Comment on #{self.ticket_id} by {self.author or 'customer'}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.author_id is not None and not self.is_internal:
            # The first public agent reply stamps the ticket; the filter keeps the earliest one.
            Ticket.objects.filter(pk=self.ticket_id, first_response_at__isnull=True).update(
                first_response_at=self.created_at
            )

    def clean(self) -> None:
        if self.is_internal and self.author_id is None:
            raise ValidationError({"is_internal": "Only agents can write internal notes."})
