# context_processors.py

from core.models import Notification
from .utils import get_user_notifications




# context_processors.py
def notifications(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}



def notification_context(request):
    if request.user.is_authenticated:
        unread_count = get_user_notifications(request.user, unread_only=True).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}



