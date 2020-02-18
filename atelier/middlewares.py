from . import models

def notifications_middleware(get_response):

    def middleware(request):
        if not request.user.is_anonymous:
            count = models.Notification.objects.filter(user=request.user, read=False).count()
            request.notification_count = count
        response = get_response(request)
        return response

    return middleware