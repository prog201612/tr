#-*- coding: utf-8 -*-
import os
from django import forms
from django.contrib import admin
from django.shortcuts import redirect, reverse
from django.http import HttpResponseRedirect
from django.urls import path

from tr.settings import BASE_DIR
from atelier.views import get_pdf_form_view

# GLOBAL ACTIONS

def export_csv_action(self, request, queryset):
    # https://stackoverflow.com/questions/14487690/get-class-name-for-empty-queryset-in-django
    f_name = 'csv/%s.csv' % queryset.model.__name__
    file = open(os.path.join(BASE_DIR, 'static/%s' % f_name), "w")
    for row in queryset.values():
        # Passem a string cada valor, el separem per ;
        line = ";".join( [str(value) for value in row.values()] )
        file.write(line + '\r\n')
    file.close()
    return get_pdf_form_view(request, action='/', titol='Exportado a CSV', files=[f_name,], url_destination='/')

# Site wide actions
# https://docs.djangoproject.com/en/2.2/ref/contrib/admin/actions/#making-actions-available-site-wide
# admin.site.add_action(export_csv_action, 'Exportar_a_csv')


# GLOBAL CLASSES

class PCRModelAdmin(admin.ModelAdmin):
    # default_filters = ('level=9',)

    def changelist_view(self, request, *args, **kwargs):
        """ Implement default_filters on admin """
        if getattr(self, 'default_filters', False):
            # request.META: dictionary width HTTP headers:
            # https://docs.djangoproject.com/en/3.0/ref/request-response/#django.http.HttpRequest.META
            url_split = request.META['HTTP_REFERER'].split('?')
            print("[PCR] - glog::admin::changelist_view", request.GET)
            # if url_split seams: ['http://localhost:8000/admin/glob/account/', 'level=9'] have filter applied
            if len(url_split) < 2: 
                # /admin/glob/account/?level=9
                filters = []
                for filter in self.default_filters:
                    key = filter.split('=')[0]
                    if not (key in request.GET):
                        filters.append(filter)
                if filters:
                    # Whe add the actual GET params. On popup for example: {'_to_field': ['id'], '_popup': ['1']}
                    params = [f"{item}={request.GET[item]}" for item in request.GET]
                    params += filters
                    url = reverse('admin:%s_%s_changelist' % (self.model._meta.app_label, self.model._meta.model_name))
                    return HttpResponseRedirect("%s?%s" % (url, "&".join(params)))
        return super().changelist_view(request, *args, **kwargs)