from django.contrib import admin

from atelier.models import Gasto, Ejercicio
from .base import PCRModelAdmin

# F i l t e r s

class FiltroGastosPorEjercicio(admin.SimpleListFilter):
    """ Filtrar gastos por ejercicio """
    title = 'Ejercicio'
    parameter_name = 'ejercicio'

    def lookups(self, request, model_admin):
        queryset = Ejercicio.objects.all().order_by('-nombre')
        ref_list = []
        for ref in queryset:
            item = (ref.id, ref.nombre)
            if not item in ref_list:
                ref_list.append(item)
        return ref_list

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(ejercicio=self.value())

# A d m i n

@admin.register(Gasto)
class GastosAdmin(PCRModelAdmin):
    list_display = ["nombre", "setiembre_", "octubre_", "noviembre_", "diciembre_", "enero_", "febrero_", "marzo_", "abril_", "mayo_", "junio_", "julio_", "agosto_", "total_", "descripcion", "cuenta", ]
    list_filter = [FiltroGastosPorEjercicio,]
    default_filters = [
        f"ejercicio={Ejercicio.objects.all().order_by('-nombre').first().id}", 
    ]
    change_list_template = "atelier/gastos_change_list.html"
    total_functions = {'setiembre': sum, 'octubre': sum, 'noviembre': sum, 'diciembre': sum, 'enero': sum, 'febrero': sum, 'marzo': sum, 'abril': sum, 'mayo': sum, 'junio': sum, 'julio': sum, 'agosto': sum, 'total': sum, }

admin.site.register(Ejercicio)