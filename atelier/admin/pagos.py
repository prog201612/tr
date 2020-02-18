#-*- coding: utf-8 -*-
from django.contrib import admin

from atelier.models import Pago, PagoNoCaja

#########
# PAGOS ######################################################
#########

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido_id', 'caja', 'clienta', 'desc', 'dia', 'importe_')
    date_hierarchy = 'dia'
    search_fields = ['pedido__id', 'pedido__consumidor__nombre', 'desc', 'importe']

    # EXTRA LIST FIELDS ######################################
    def pedido_id(self, obj):
        return obj.pedido.pk
    pedido_id.short_description = "Nº Pedido"

    def clienta(self, obj):
        return obj.pedido.consumidor.nombre
    pedido_id.short_description = "Clienta"

    # PERMISSIONS ############################################
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


#################
# PAGOS NO CAJA ######################################################
#################

@admin.register(PagoNoCaja)
class PagoNoCajaAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido_id', 'clienta', 'desc', 'dia', 'importe_')
    date_hierarchy = 'dia'
    search_fields = ['pedido__id', 'pedido__consumidor__nombre', 'desc', 'importe']

    # EXTRA LIST FIELDS ######################################
    def pedido_id(self, obj):
        return obj.pedido.pk
    pedido_id.short_description = "Nº Pedido"

    def clienta(self, obj):
        return obj.pedido.consumidor.nombre
    pedido_id.short_description = "Clienta"

    # PERMISSIONS ############################################
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
