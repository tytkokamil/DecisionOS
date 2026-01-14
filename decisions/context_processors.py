from django.db.models import Count
from .models import Notification


def notifications(request):
    """Expose unread notification count to templates."""
    if not request.user.is_authenticated:
        return {"unread_notifications_count": 0}
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return {"unread_notifications_count": count}
