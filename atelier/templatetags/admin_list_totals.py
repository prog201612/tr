
from django.template import Library

from atelier.utils import get_currency_representation

register = Library()

def totals_row(cl):
    total_functions = getattr(cl.model_admin, 'total_functions', {})
    totals = []
    for field_name in cl.list_display:
        field_name = field_name.replace('_', '')
        #print("[ H e Y ] -> ", field_name)
        if field_name in total_functions:
            # result_list: és el QuerySet del ModelAdmin.
            #         Exemple:  <QuerySet [<MaterialsStock: M67 - 121 - 27 - BOB - [3.00]>,
            # values: array amb els valors del camp a totalitzar.
            #         Exemple:  [Decimal('3.00'), Decimal('4.00'), Decimal('5.00')]
            values = [getattr(i, field_name) for i in cl.result_list]
            # Totals: array amb una fila per cada columna del QuerySet,
            #         on apliquem per a cada columna de total_functions la funció
            #         que té associada, per exemple sum, a l'array de valors (values)
            total_str = get_currency_representation(total_functions[field_name](values), positive_color='aqua', negative_color='fuchsia')
            totals.append(total_str)
        elif field_name == 'actioncheckbox' and total_functions:
            totals.append('Totals')
        else:
            totals.append('')
    return {'cl': cl, 'totals_row': totals, 'totals_count': len(total_functions)}
totals_row = register.inclusion_tag("admin/pcr_admin_list_totals.html")(totals_row)