from django.contrib import admin

from atelier.models import Consumidor 

##############
# CONSUMIDOR ##################################################
##############

@admin.register(Consumidor)
class ConsumidorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'telefono')
    search_fields = ('nombre',)
    actions = ['import_from_csv']