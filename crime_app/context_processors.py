from .models import Notification

def officer_notifications(request):
    """
    Make notification data available on all officer pages.
    """
    if request.user.is_authenticated and hasattr(request.user, 'officer'):
        officer = request.user.officer
        unread_count = officer.notifications.filter(is_read=False).count()
        recent_notifications = officer.notifications.order_by('-created_at')[:5]
    else:
        unread_count = 0
        recent_notifications = []

    return {
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
    }
