#-*- coding: utf-8 -*-
from django import forms
from django.contrib import admin
from django.contrib import messages
# from django.core.mail import EmailMessage
from django.shortcuts import redirect, reverse
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.utils.safestring import mark_safe

from atelier.models import Pedido, Pago, Caja, Apuntes, get_week_by_date, \
                    Notification, get_year_week_int_by_date
from atelier.models import NOTIFICATION_TYPE_BOX_CLOSED
from atelier.helpers import send_mailgun_mail
from tr.settings import BASE_DIR, MAILGUN_AUTHORIZED_LIST


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
@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'year', 'semana', 'get_monday_by_week', 'saldo_anterior', 'saldo_cierre', \
                       'cerrada', 'caja_siguiente', 'caja_anterior_link', 'caja_siguiente_link', \
                       'get_total_pagos_str', 'get_total_apuntes_entrada_str', 'get_total_apuntes_salida_str')
    inlines = [ ApuntesInline, PagoReadOnlyInline ]
    list_display = ('id', 'year', 'semana', 'get_monday_by_week', 'saldo_anterior_', 'saldo_cierre_', 'cerrada')
    actions = [ 'close_box' ]
    fields = (
        ('year', 'semana', 'get_monday_by_week',),
        ('saldo_anterior', 'saldo_cierre'),
        ('caja_siguiente', 'cerrada'),
        ('caja_anterior_link', 'caja_siguiente_link'),
        ('get_total_pagos_str', 'get_total_apuntes_entrada_str', 'get_total_apuntes_salida_str'),
    )

    # OVERRIDES
    
    def get_readonly_fields(self, request, obj=None):
        """ semana només es pot modificar al afegir un nou registre """
        if obj: # editing an existing object
            fields = ()
            if not obj.cerrada:
                if ('get_provisional_saldo_anterior_str', 'get_provisional_saldo_str') not in self.fields:
                    self.fields += (('get_provisional_saldo_anterior_str', 'get_provisional_saldo_str'),)
                fields += ('get_provisional_saldo_anterior_str', 'get_provisional_saldo_str',)
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

    def has_module_permission(self, request):
        return request.user.has_perm('atelier.view_caja')

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
            week = get_year_week_int_by_date(now())
            cajas_anterior = caja.caja_anterior.all()
            if caja.cerrada:
                self.message_user(request, 'Esta caja ya está cerrada...', level=messages.WARNING)
            elif week <= caja.get_year_week_int():
                self.message_user(request, 'La semana tiene que estar finalizada para poder cerrar la caja...', level=messages.WARNING)
            elif len(cajas_anterior) > 0 and not cajas_anterior[0].cerrada:
                self.message_user(request, 'La caja anterior a la seleccionada no puede estar abierta...', level=messages.WARNING)
            else:
                caja.cerrada = True
                if len(cajas_anterior) > 0:
                    caja.saldo_anterior = cajas_anterior[0].saldo_cierre
                caja.saldo_cierre = caja.get_saldo_cierre()
                caja.save()
                # Creem la notificació
                desc = f'<a href="/atelier/caja/{caja.pk}/change/">Caja Nº: {caja.pk}</a>'
                Notification.new_notification( NOTIFICATION_TYPE_BOX_CLOSED, desc )
                # Caja.objects.create(saldo_anterior=caja.saldo_cierre)
                self.message_user(request, 'Se ha cerrado la caja y se ha informado a oficina via email...', level=messages.INFO)
                # enviem correu a officina
                send_mailgun_mail(
                    to_list=MAILGUN_AUTHORIZED_LIST, 
                    subject_str="Atelier Caja cerrada...", 
                    text_str="Se ha cerrado la caja: " + str(caja), 
                    files_list=[])
        else:
            self.message_user(request, 'Selecciona un y solo un Pedido...', level=messages.WARNING)

        # return redirect(reverse_lazy('atelier:sales_compare_years'))
    close_box.short_description = "Cerrar la caja..."
