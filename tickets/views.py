import mimetypes
from pathlib import PurePath

from django.http import Http404, HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from tickets.models import Comment, Ticket


def attachment(request: HttpRequest, comment_id: int) -> HttpResponseRedirect:
    """Redirect to a 60 s presigned download, only for tickets this user may see (else 404)."""
    if not request.user.has_perm("tickets.view_comment"):
        raise Http404
    comment = get_object_or_404(
        Comment.objects.filter(ticket__in=Ticket.objects.visible_to(request.user)).exclude(
            attachment=""
        ),
        pk=comment_id,
    )
    ext = PurePath(comment.attachment.name).suffix
    filename = f"ticket-{comment.ticket_id}-{comment.pk}{ext}"
    url = comment.attachment.storage.url(
        comment.attachment.name,
        parameters={
            # Always a download with our own name, never rendered inline from the bucket.
            "ResponseContentDisposition": f'attachment; filename="{filename}"',
            "ResponseContentType": mimetypes.guess_type(f"x{ext}")[0] or "application/octet-stream",
        },
    )
    return HttpResponseRedirect(url)
