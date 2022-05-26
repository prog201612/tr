from django.urls import path

from .views import sales_compare_years_report, consumidor_import_from_csv, \
                   consumidor_to_csv_form, pedido_to_csv_form, pedido_import_from_csv, \
                   pdf_pedido, pdf_pedido_pagos, gastos_from_csv_form, gastos_import_from_csv

atelier_patterns = ([
    # path('sales-compare-years/', sales_compare_years, name='sales_compare_years'),
    path('sales-compare-years-report/', sales_compare_years_report, name='sales_compare_years_report'),

    path('consumidor-to-csv/', consumidor_to_csv_form, name='consumidor-to-csv'),
    path('consumidor-import-from-csv/', consumidor_import_from_csv, name='consumidor_import_from_csv'),

    path('pedido-to-csv/', pedido_to_csv_form, name='pedido-to-csv'),
    path('pedido-import-from-csv/', pedido_import_from_csv, name='pedido_import_from_csv'),

    path('pdf-pedido/<int:pk>', pdf_pedido, name="pdf-pedido"),
    path('pdf-pedido-pagos/<int:pk>', pdf_pedido_pagos, name="pdf-pedido-pagos"),

    path('gastos-from-csv/', gastos_from_csv_form, name='gastos-from-csv'),
    path('gastos-import-from-csv/', gastos_import_from_csv, name='gastos_import_from_csv'),

], 'atelier')