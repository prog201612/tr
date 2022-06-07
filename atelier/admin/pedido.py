#-*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import path, reverse_lazy

from atelier.models import Consumidor, Pedido, Pago, Articulo, Caja, PagoNoCaja, \
                           Notification, get_year_week_int_by_date
from atelier.models import NOTIFICATION_TYPE_SEND_ORDER_TO_WORKSHOP
from atelier.reports import print_order_report, print_order_payments
from atelier.views import get_pdf_form_view
from atelier.helpers import send_mailgun_mail
from tr.settings import BASE_DIR, MAILGUN_AUTHORIZED_LIST
from atelier.forms import SalesCompareYearsForm

from .admin_global import PCRModelAdmin


##########
# PEDIDO ######################################################
##########

# INLINES
class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0
    readonly_fields = ('caja',)
    verbose_name_plural = "Pagos en efectivo de cajas cerradas"

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super(PagoInline, self).get_queryset(request)
        return qs.filter(caja__cerrada=True)


class PagoInlineEdit(admin.TabularInline):
    model = Pago
    extra = 0
    readonly_fields = ('caja', 'recibo_creado', )
    verbose_name_plural = "Pagos en efectivo"

    def get_queryset(self, request):
        qs = super(PagoInlineEdit, self).get_queryset(request)
        # return qs.filter( Q(caja__cerrada=False) | Q(forma_pago__gt=1) )
        return qs.filter(caja__cerrada=False, recibo_creado=False)

    def has_add_permission(self, request, obj=None):
        if not request.user.has_perm('atelier.add_pedido'):
            return False
        if obj:
            return obj.activo
        return True

    def has_delete_permission(self, request, obj=None):
        if not request.user.has_perm('atelier.delete_pedido'):
            return False
        if obj:
            return obj.activo
        return True

    def has_change_permission(self, request, obj=None):
        if not request.user.has_perm('atelier.change_pedido'):
            return False
        if obj:
            return obj.activo
        return True


class PagoInlineRecivo(admin.TabularInline):
    model = Pago
    extra = 0
    readonly_fields = ('caja', 'recibo_creado', )
    verbose_name_plural = "Pagos en efectivo con recibo entregado"

    def get_queryset(self, request):
        qs = super(PagoInlineRecivo, self).get_queryset(request)
        # return qs.filter( Q(caja__cerrada=False) | Q(forma_pago__gt=1) )
        return qs.filter(caja__cerrada=False, recibo_creado=True)

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


class PagoNoCajaInline(admin.TabularInline):
    model = PagoNoCaja
    extra = 0
    readonly_fields = ('recibo_creado', )

    def has_add_permission(self, request, obj=None):
        if not request.user.has_perm('atelier.add_pedido'):
            return False
        if obj:
            return obj.activo
        return True

    def has_delete_permission(self, request, obj=None):
        if not request.user.has_perm('atelier.delete_pedido'):
            return False
        if obj:
            return obj.activo
        return True

    def has_change_permission(self, request, obj=None):
        if not request.user.has_perm('atelier.change_pedido'):
            return False
        if obj:
            return obj.activo
        return True

    def get_queryset(self, request):
        qs = super(PagoNoCajaInline, self).get_queryset(request)
        return qs.filter(recibo_creado=False)


class PagoNoCajaInlineRecivo(admin.TabularInline):
    model = PagoNoCaja
    extra = 0
    readonly_fields = ('recibo_creado', )
    verbose_name_plural = "Pagos no a caja con recibo entregado"

    def get_queryset(self, request):
        qs = super(PagoNoCajaInlineRecivo, self).get_queryset(request)
        return qs.filter(recibo_creado=True)

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


class ArticuloInline(admin.TabularInline):
    model = Articulo
    extra = 0
    readonly_fields = ()

    def has_add_permission(self, request, obj=None):
        if not request.user.has_perm('atelier.add_pedido'):
            return False
        if obj:
            return obj.activo
        return True

    def has_delete_permission(self, request, obj=None):
        if not request.user.has_perm('atelier.delete_pedido'):
            return False
        if obj:
            return obj.activo
        return True

    def has_change_permission(self, request, obj=None):
        if not request.user.has_perm('atelier.change_pedido'):
            return False
        if obj:
            return obj.activo
        return True

'''
# FILTERS

class ActivoSimpleListFilter(admin.SimpleListFilter):
    title = 'Activo'
    parameter_name = 'activo'

    def value(self):
        value = super(ActivoSimpleListFilter, self).value()
        if value is None:
            value = 's'
        return str(value)

    def lookups(self, request, model_admin):
        return (
            ('s', 'Si'),
            ('n', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(activo=self.value()=='s')
'''

# ADMIN
@admin.register(Pedido)
class PedidoAdmin(PCRModelAdmin):
    list_display = ('id', 'consumidor_nombre', 'dia', 'dia_entrega', 'dia_evento', 'total_pagado_', 'importe_total_', 'email_enviado', 'activo')
    # list_filter = [ActivoSimpleListFilter,]
    list_filter = ['activo',]
    default_filters = ('activo__exact=1',)
    search_fields = ('id', 'consumidor__nombre',)
    inlines = [ ArticuloInline, PagoInline, PagoInlineEdit, PagoNoCajaInline, PagoInlineRecivo, PagoNoCajaInlineRecivo, ]
    actions = [ 'email_orders_as_pdf', 'order_report', 'order_payments_list', 'mark_as_completed']
    raw_id_fields = ("consumidor",)
    readonly_fields = ('id', 'activo', 'importe_total_', 'total_pagado_', 'pendiente_', 'iva', )
    change_list_template = "atelier/pedidos_change_list.html"
    change_form_template = "atelier/pedidos_change_form.html"
    fields = (
        'id',
        ('consumidor', 'activo'),
        ('dia', 'dia_evento'),
        ('dia_pedido', 'dia_entrega'),
        'lugar_evento',
        ('nos_conocio', 'nos_conocio_coment'),
        'variaciones',
        ('contorno_pecho_total', 'contorno_cintura'),
        ('contorno_cadera', 'largo_talle_delante'),
        ('largo_talle_espalda', 'largo_falda'),
        ('largo_chaqueta_delante', 'largo_blusa_delante'),
        ('largo_manga_chaqueta', 'largo_manga_blusa'),
        ('contorno_brazo', 'de_hombro_a_hombro'),
        ('importe_total_', 'total_pagado_', 'pendiente_', 'iva'),
    )

    # OVERRIDES

    '''
    def get_readonly_fields(self, request, obj=None):
        """ semana només es pot modificar al afegir un nou registre """
        if obj and not obj.activo: # editing an existing object
            return self.readonly_fields + ('consumidor','dia', 'dia_evento','dia_pedido', 'dia_entrega','lugar_evento',
                'variaciones','contorno_pecho_total', 'contorno_cintura','contorno_cadera', 'largo_talle_delante', 
                'largo_talle_espalda', 'largo_falda', 'largo_chaqueta_delante', 'largo_blusa_delante', 'largo_manga_chaqueta', 
                'largo_manga_blusa', 'contorno_brazo', 'de_hombro_a_hombro', 'importe_total_', 'total_pagado_', 'pendiente')
        return self.readonly_fields
    '''

    # EXTRA LIST FIELDS ##############################################
    def consumidor_nombre(self, obj):
        return obj.consumidor.nombre
    consumidor_nombre.short_description = "Nombre Clienta"


    # PERMISIONS #####################################################

    def has_delete_permission(self, request, obj=None):
        """ Si ja té pagaments fets no es pot eliminar la comanda """
        if obj:
            ret = len(obj.pagos.all()) == 0 and len(obj.pagos_no_caja.all()) == 0
            if not ret:
                self.message_user(request, 'No se pueden eliminar los pedidos que ya tienen pagos realizados...', level=messages.WARNING)
            return ret
        return True

    def has_change_permission(self, request, obj=None):
        if not request.user.has_perm('atelier.change_pedido'):
            return False
        if obj:
            return obj.activo
        return True


    # URLS / VIEWS ###########################################################

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('sales-compare-years/', self.sales_compare_years, name='sales_compare_years')
        ]
        return my_urls + urls

    def sales_compare_years(self, request):
        """ 
        Posant la vista dins del Admin i afegint la url desde get_urls podem aconseguir
        que es mostrin les dades de l'usuari a la capçalera de la pàgina igual com a
        la resta de pàgines del admin. En aquest cas després del formulari es mostra
        l'informe que està fet en una vista normal amb la url a urls.py de manera que
        es perd informació de la capçalera.
        """
        form = SalesCompareYearsForm()
        context = {
            'form':form,
            'action': '/atelier/sales-compare-years-report/',
            'url_destination': '/atelier/pedido/',
            'titol': 'Comparativa de ventas',
            'descripcio':'Comparacion de ventas de Febrero a Agosto, entre dos anyos.'
        }

        # Include common variables for rendering the admin template.
        context = {**context, **self.admin_site.each_context(request)}
        return render(request, 'atelier/pcr_form_p.html', context)

    # ACTIONS ########################################################

    # ACTION: email_orders_as_pdf
    def email_orders_as_pdf(self, request, queryset):
        print("Creating orders in pdf format...")
        file_names_list = print_order_report(queryset)
        print("Sending email width pdf's...")
        # Creem les notificacions per cada pedido enviat.
        for order in queryset:
            desc = f'<a href="/atelier/pedido/{order.pk}/change/">Pedido Nº: {order.pk}</a>'
            Notification.new_notification( NOTIFICATION_TYPE_SEND_ORDER_TO_WORKSHOP, desc )
        # Adjuntem fitxers
        files = []
        for file_name in file_names_list:
            print("[+] attaching file: " + file_name)
            files.append( ("attachment", (file_name.split("/")[-1], open(file_name,"rb").read())) )
        # Enviem
        try:
            send_mailgun_mail(
                to_list=MAILGUN_AUTHORIZED_LIST, 
                subject_str="Atelier Pedidos PDF...", 
                text_str="Atelier email sender, HTML.", 
                files_list=files)

            # Maruqem el correu com a enviat
            for order in queryset:
                order.email_enviado = True
                order.save()
            self.message_user(request, 'El correo ha sido enviado...', level=messages.INFO)
        except:
            self.message_user(request, 'Error sending email, try it later...', level=messages.ERROR)
    email_orders_as_pdf.short_description = "Email Pedidos en formato PDF..."


    # ACTION: order_payments_list
    def order_payments_list(self, request, queryset):
        if len(queryset) == 1:
            file = 'pdf/' + print_order_payments(queryset[0])
            return get_pdf_form_view(request, action='/atelier/pedido/', titol='Pagos de un Pedido', files=[file,], url_destination='/atelier/pedido/')
        else:
            self.message_user(request, 'Selecciona un y solo un Pedido...', level=messages.WARNING)
    order_payments_list.short_description = "Pagos de un Pedido (PDF)..."


    # ACTION: order_report
    def order_report(self, request, queryset):
        file_names_list = print_order_report(queryset)
        names_only_list = ['pdf/' + s.split('/')[-1] for s in file_names_list]
        return get_pdf_form_view(request, action='/atelier/pedido/', titol='Pedidos', files=names_only_list, url_destination='/atelier/pedido/')
    order_report.short_description = "Pedido en formato PDF..."


    # ACTION: mark_as_completed
    def mark_as_completed(self, request, queryset):
        if len(queryset) == 1:
            pedido = queryset[0]
            if not pedido.activo:
                self.message_user(request, 'El pedido seleccionado ya està completado...', level=messages.WARNING)
            elif pedido.total_pagado() != pedido.importe_total():
                self.message_user(request, 'El importe pagado no coincide con el total del pedido...', level=messages.WARNING)
            else:
                # marquem el Pedido com a completat
                pedido.activo = False
                pedido.save()
        else:
            self.message_user(request, 'Selecciona un y solo un Pedido...', level=messages.WARNING)

    mark_as_completed.short_description = "Marcar el pedido como completado..."


    # OVERRIDES
    '''
    def save_model(self, request, obj, form, changed):
        # https://stackoverflow.com/questions/14126371/in-django-how-to-override-the-save-and-continue-feature
        #super(PedidoAdmin, self).save_model(request, obj, form, changed)
        if '_pdf_pedido' in request.POST:
            # add your code here
            print("[ p.c.r. ] - Pedido::save_model")
            print( dir(request) )
            url = reverse_lazy(f'atelier:pdf-pedido', kwargs={ 'pk': obj.pk }) 
            request['post_url_continue'] = url
            #return redirect( reverse_lazy(f'atelier:pdf-pedido', kwargs={ 'pk': obj.pk }) )
            result = super(PedidoAdmin, self).change_view(request, str(obj.pk), form, changed )
            result['Location'] = url
            return result
    '''

    # Al change_list de Pedidos volem que al premer botons PDF es guardi abans de crear el pdf
    
    def response_add(self, request, obj, post_url_continue=None):
        if '_pdf_pedido' in request.POST:
            url = reverse_lazy(f'atelier:pdf-pedido', kwargs={ 'pk': obj.pk }) 
            return redirect(url)
        elif '_pdf_pedido_pagos' in request.POST:
            url = reverse_lazy(f'atelier:pdf-pedido-pagos', kwargs={ 'pk': obj.pk }) 
            return redirect(url)
        return super(PedidoAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if '_pdf_pedido' in request.POST:
            url = reverse_lazy(f'atelier:pdf-pedido', kwargs={ 'pk': obj.pk }) 
            return redirect(url)
        elif '_pdf_pedido_pagos' in request.POST:
            url = reverse_lazy(f'atelier:pdf-pedido-pagos', kwargs={ 'pk': obj.pk }) 
            return redirect(url)
        return super(PedidoAdmin, self).response_change(request, obj)
    
        

