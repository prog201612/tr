#-*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.safestring import mark_safe

from atelier.models import Notification, NotificationTypeXUser

from .admin_global import PCRModelAdmin


#################
# NOTIFICATIONS #
#################

@admin.register(NotificationTypeXUser)
class NotificationTypeXUserAdmin(admin.ModelAdmin):
    list_display = ("user", "notification_type")
    list_filter = ("user",)


@admin.register(Notification)
class NotificationAdmin(PCRModelAdmin):
    list_display = ("user", "notification_type", "date_time", "link", "read")
    list_editable = ("read", )
    readonly_fields = ("user", "notification_type", "date_time", "link")
    fields = ("user", "notification_type", "date_time", "link", "read")
    list_filter = ['read',]
    default_filters = ['read__exact=0',]

    def link(self, obj):
        return mark_safe(obj.description)
    link.short_description = "link"

    def get_queryset(self, request):
        """ només els usuaris poden veure les seves notificacions excepte el superusuari"""
        # https://docs.djangoproject.com/en/3.0/ref/contrib/admin/#django.contrib.admin.ModelAdmin.get_queryset
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)