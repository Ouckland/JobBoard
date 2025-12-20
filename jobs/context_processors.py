from .models import Notification

def user_notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        unread_count = notifications.filter(is_read=False, recipient=request.user).count()
        return {
            'notifications': notifications,
            'unread_count': unread_count
        }
    return {}


# from .models import Notification

# def unread_notification_count(request):
#     if request.user.is_authenticated:
#         count = Notification.objects.filter(recipient=request.user, is_read=False).count()
#         return {'unread_count': count}
#     return {}
