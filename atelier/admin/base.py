
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

# P C R    M o d e l   A d m i n

class PCRModelAdmin(admin.ModelAdmin):
    # default_filters = ('level=9',)

    def changelist_view(self, request, *args, **kwargs):
        """ Implement default_filters on admin """
        if getattr(self, 'default_filters', False):
            # request.META: dictionary width HTTP headers:
            # https://docs.djangoproject.com/en/3.0/ref/request-response/#django.http.HttpRequest.META
            url_split = ""
            if 'HTTP_REFERER' in request.META:
                url_split = request.META['HTTP_REFERER'].split('?')
            #print("[PCR] - glog::admin::changelist_view", request.GET)
            # if url_split seams: ['http://localhost:8000/admin/glob/account/', 'level=9'] have filter applied
            if len(url_split) < 2: 
                # /admin/glob/account/?level=9
                filters = []
                for filter in self.default_filters:
                    key = filter.split('=')[0]
                    if not (key in request.GET):
                        filters.append(filter)
                #print("---- Filters:", filters)
                if filters:
                    # Whe add the actual GET params. On popup for example: {'_to_field': ['id'], '_popup': ['1']}
                    params = [f"{item}={request.GET[item]}" for item in request.GET]
                    params += filters
                    url = reverse('admin:%s_%s_changelist' % (self.model._meta.app_label, self.model._meta.model_name))
                    return HttpResponseRedirect("%s?%s" % (url, "&".join(params)))
        return super().changelist_view(request, *args, **kwargs)