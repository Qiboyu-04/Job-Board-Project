from .models import Notification


def unread_notifications(request):
    """
    Context processor to add unread notification count to all templates
    """
    unread_count = 0
    
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
    
    return {
        'unread_notifications_count': unread_count,
    }
