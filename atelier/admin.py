#-*- coding: utf-8 -*-
import os
# import datetime
from django import forms
from django.contrib import admin
from django.contrib import messages
# from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.db.models import Q


from .models import Consumidor, Pedido, Pago, Articulo, Caja, Apuntes, PagoNoCaja, get_week_by_date
from .reports import print_order_report, print_order_payments
from .views import get_pdf_form_view
from .helpers import send_mailgun_mail
from tr.settings import BASE_DIR


# Register your models here.

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


##############
# CONSUMIDOR ##################################################
##############

class ConsumidorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'telefono')
    search_fields = ('nombre',)
    actions = ['import_from_csv']

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
    readonly_fields = ('caja',)
    verbose_name_plural = "Pagos en efectivo"

    def get_queryset(self, request):
        qs = super(PagoInlineEdit, self).get_queryset(request)
        # return qs.filter( Q(caja__cerrada=False) | Q(forma_pago__gt=1) )
        return qs.filter(caja__cerrada=False)

    def has_add_permission(self, request, obj=None):
        if obj:
            return obj.activo
        return True

    def has_delete_permission(self, request, obj=None):
        if obj:
            return obj.activo
        return True

    def has_change_permission(self, request, obj=None):
        if obj:
            return obj.activo
        return True


class PagoNoCajaInline(admin.TabularInline):
    model = PagoNoCaja
    extra = 0

    def has_add_permission(self, request, obj=None):
        if obj:
            return obj.activo
        return True

    def has_delete_permission(self, request, obj=None):
        if obj:
            return obj.activo
        return True

    def has_change_permission(self, request, obj=None):
        if obj:
            return obj.activo
        return True


class ArticuloInline(admin.TabularInline):
    model = Articulo
    extra = 0
    readonly_fields = ()

    def has_add_permission(self, request, obj=None):
        if obj:
            return obj.activo
        return True

    def has_delete_permission(self, request, obj=None):
        if obj:
            return obj.activo
        return True

    def has_change_permission(self, request, obj=None):
        if obj:
            return obj.activo
        return True


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


# ADMIN
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'consumidor_nombre', 'dia', 'dia_entrega', 'dia_evento', 'total_pagado_', 'importe_total_', 'email_enviado', 'activo')
    list_filter = [ActivoSimpleListFilter,]
    search_fields = ('id', 'consumidor__nombre',)
    inlines = [ ArticuloInline, PagoInline, PagoInlineEdit, PagoNoCajaInline ]
    actions = [ 'email_orders_as_pdf', 'order_report', 'order_payments_list', 'mark_as_completed']
    raw_id_fields = ("consumidor",)
    readonly_fields = ('id', 'activo', 'importe_total_', 'total_pagado_', 'pendiente')
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
        ('importe_total_', 'total_pagado_', 'pendiente'),
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
        if obj:
            return obj.activo
        return True

    # ACTIONS ########################################################

    # ACTION: email_orders_as_pdf
    def email_orders_as_pdf(self, request, queryset):
        print("Creating orders in pdf format...")
        file_names_list = print_order_report(queryset)
        print("Sending email width pdf's...")
        # Adjuntem fitxers
        files = []
        for file_name in file_names_list:
            print("[+] attaching file: " + file_name)
            files.append( ("attachment", (file_name.split("/")[-1], open(file_name,"rb").read())) )
        # Enviem
        try:
            send_mailgun_mail(
                to_list=["pere@teresaripoll.com"], 
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


#########
# PAGOS ######################################################
#########

class PagoAdmin(admin.ModelAdmin):
    list_display = ('pedido_id', 'desc', 'dia', 'importe_')
    date_hierarchy = 'dia'

    # EXTRA LIST FIELDS ######################################
    def pedido_id(self, obj):
        return obj.pedido.pk
    pedido_id.short_description = "Nº Pedido"


#######
# CAJA ######################################################
#######

# INLINES

class ApuntesAdminForm(forms.ModelForm):
    ''' https://docs.djangoproject.com/en/2.2/ref/forms/validation/#cleaning-a-specific-field-attribute '''

    def clean_dia(self):
        dia = self.cleaned_data['dia']
        caja = self.cleaned_data['caja']
        week = get_week_by_date(dia)
        if week != caja.semana:
            raise forms.ValidationError("La fecha està fuera de la semana de la caja actual: " + str(caja.semana) )

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return dia

    def clean_salida(self):
        print(self.cleaned_data)
        entrada = self.cleaned_data['entrada']
        salida = self.cleaned_data['salida']
        if entrada != 0 and salida != 0:
            raise forms.ValidationError("Un mismo apunto no puede tener la entrada y la salida diferente de zero.")
        return salida


class ApuntesInline(admin.TabularInline):
    model = Apuntes
    extra = 0
    readonly_fields = ()
    form = ApuntesAdminForm

    def has_add_permission(self, request, obj=None):
        if obj is not None: # and "cerrada" in obj:
            return not obj.cerrada
        return True

    def has_delete_permission(self, request, obj=None):
        if obj is not None: # and "cerrada" in obj:
            return not obj.cerrada
        return True

    def has_change_permission(self, request, obj=None):
        if obj:
            return not obj.cerrada
        return True

    '''
    def get_readonly_fields(self, request, obj=None):
        """ semana només es pot modificar al afegir un nou registre """
        if obj is not None and obj.cerrada: # editing an existing object, and "cerrada" in obj
            return self.readonly_fields + ('dia', 'concepto','entrada', 'salida',)
        return self.readonly_fields
    '''


class PagoReadOnlyInline(admin.TabularInline):
    model = Pago
    extra = 0
    readonly_fields = ('pedido', 'dia', 'desc', 'importe', 'caja',) # 'forma_pago', 
    verbose_name_plural = "Pagos en efectivo"

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

# Caja

class CajaAdmin(admin.ModelAdmin):
    readonly_fields = ('year', 'semana', 'get_monday_by_week', 'saldo_anterior', 'saldo_cierre', \
                       'cerrada', 'caja_siguiente', 'caja_anterior_link', 'caja_siguiente_link', \
                       'get_total_pagos', 'get_total_apuntes_entrada', 'get_total_apuntes_salida', \
                       'get_provisional_saldo_anterior', 'get_provisional_saldo')
    inlines = [ ApuntesInline, PagoReadOnlyInline ]
    list_display = ('year', 'semana', 'get_monday_by_week', 'saldo_anterior_', 'saldo_cierre_', 'cerrada')
    actions = [ 'close_box' ]
    fields = (
        ('year', 'semana', 'get_monday_by_week',),
        ('saldo_anterior', 'saldo_cierre'),
        ('caja_siguiente', 'cerrada'),
        ('caja_anterior_link', 'caja_siguiente_link'),
        ('get_total_pagos', 'get_total_apuntes_entrada', 'get_total_apuntes_salida'),
        ('get_provisional_saldo_anterior', 'get_provisional_saldo'),
    )

    # OVERRIDES
    
    def get_readonly_fields(self, request, obj=None):
        """ semana només es pot modificar al afegir un nou registre """
        if obj: # editing an existing object
            fields = ()
            if not obj.cerrada:
                if ('get_provisional_saldo_anterior', 'get_provisional_saldo') not in self.fields:
                    self.fields += (('get_provisional_saldo_anterior', 'get_provisional_saldo'),)
                fields += ('get_provisional_saldo_anterior', 'get_provisional_saldo',)
            fields += ('semana',)
            return self.readonly_fields + fields
        return self.readonly_fields
    

   # def save_model(self, request, obj, form, change):
        # obj.user = request.user
        # print("GUARDEM: ApuntesInline")
        # super().save_model(request, obj, form, change)

    '''
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            # Do something with `instance`
            if isinstance(instance, Apuntes):
                week = get_week_by_date(instance.dia)
                if instance.entrada != 0 and instance.salida != 0:
                    self.message_user(request, 'No se admite un valor de entrada y otro de salida en el mismo apunte...', level=messages.ERROR)
                elif instance.caja.semana != week:
                    self.message_user(request, 'El dia del apunte está fuera de la semana assignada a la caja...', level=messages.ERROR)
                else:
                    instance.save()
            else:
                instance.save()
        formset.save_m2m()
    '''

    # PERMISIONS

    def has_change_permission(self, request, obj=None):
        if obj:
            return not obj.cerrada
        return True

    def has_add_permission(self, request, obj=None):
        today = now()
        week = get_week_by_date(today)
        cajas = Caja.objects.filter(year=today.year, semana=week)
        return len(cajas) == 0

    def has_delete_permission(self, request, obj=None):
        # if obj and request.user.is_superuser:
        if obj and obj.caja_siguiente is not None:
            # Si ja té una caixa següent no es pot eliminar
            self.message_user(request, 'Las cajas que han sido enlazadas con otra caja no se pueden eliminar...', level=messages.WARNING)
            return False
        elif obj and len( obj.pagos.all() ) > 0:
            # Si ja hi té pagaments assignats tampoc
            self.message_user(request, 'Las cajas que tienen pagos en efecivo assignados no se pueden eliminar...', level=messages.WARNING)
            return False
        return True

    # ACTIONS

    # ACTION: 
    def close_box(self, request, queryset):
        ''' 
            Una caixa es pot tancar si:
            1) La caixa està oberta
            2) La setmana on opera ja està finalitzada
            3) La seva caixa_anterior està tencada
        '''
        if len(queryset) == 1:
            # Caixa actual
            caja = queryset[0]
            week = get_week_by_date(now())
            cajas_anterior = caja.caja_anterior.all()
            if caja.cerrada:
                self.message_user(request, 'Esta caja ya está cerrada...', level=messages.WARNING)
            elif week <= caja.semana:
                self.message_user(request, 'La semana tiene que estar finalizada para poder cerrar la caja...', level=messages.WARNING)
            elif len(cajas_anterior) > 0 and not cajas_anterior[0].cerrada:
                self.message_user(request, 'La caja anterior a la seleccionada no puede estar abierta...', level=messages.WARNING)
            else:
                caja.cerrada = True
                if len(cajas_anterior) > 0:
                    caja.saldo_anterior = cajas_anterior[0].saldo_cierre
                caja.saldo_cierre = caja.get_saldo_cierre()
                caja.save()
                # Caja.objects.create(saldo_anterior=caja.saldo_cierre)
                self.message_user(request, 'Se ha cerrado la caja y se ha informado a oficina via email...', level=messages.INFO)
                # enviem correu a officina
                send_mailgun_mail(
                    to_list=["pere@teresaripoll.com"], 
                    subject_str="Atelier Caja cerrada...", 
                    text_str="Se ha cerrado la caja: " + str(caja), 
                    files_list=[])
        else:
            self.message_user(request, 'Selecciona un y solo un Pedido...', level=messages.WARNING)

        # return redirect(reverse_lazy('atelier:sales_compare_years'))
    close_box.short_description = "Cerrar la caja..."



############
# REGISTERS ***************************************************
############

admin.site.register(Consumidor, ConsumidorAdmin)
admin.site.register(Pedido, PedidoAdmin)
# admin.site.register(Pago, PagoAdmin)
admin.site.register(Caja, CajaAdmin)

# Site wide actions
# https://docs.djangoproject.com/en/2.2/ref/contrib/admin/actions/#making-actions-available-site-wide
# admin.site.add_action(export_csv_action, 'Exportar_a_csv')
