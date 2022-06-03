#-*- coding: utf-8 -*-
import os
from datetime import timedelta

from django.utils.dateparse import parse_datetime
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Sum
from django.contrib import messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseBadRequest

from tr.settings import BASE_DIR
from .forms import GastosGenerarFacturacionForm, SalesCompareYearsForm, GetCSVFileForm, ImportGastosFromCSV
from .models import Articulo, Ejercicio, Pedido
from .reports import print_order, print_order_payments
from .helpers import handle_uploaded_file, import_csv_consumidor, import_csv_gasto, import_csv_pedido, \
                     getCurrencyHtml

# Create your views here.

###################################
# CSV: Consumidor, esportar a csv #
###################################
def csv_form(request, action, title):
    form = GetCSVFileForm()
    context = {
        'form':form,
        'action': action,
        'url_destination': '/',
        'titol': 'Importar CSV',
        'descripcio':'Importar %s desde un fichero en formato CSV.' % title
    }
    return render(request, 'atelier/pcr_form_p.html', context)  


# Consumidor

@staff_member_required
def consumidor_to_csv_form(request):
    if request.user.is_superuser:
        return csv_form(request, '/atelier/consumidor-import-from-csv/', 'Consumidor')          
    else:
        return HttpResponseBadRequest('Error 404')


@staff_member_required
def consumidor_import_from_csv(request):
    # @user_passes_test(lambda u: u.is_superuser)
    if request.user.is_superuser:
        # Guardem el fitxer a disc
        file_name = handle_uploaded_file(request.FILES['csv_file'])
        # Importem les dades del fitxer csv
        import_csv_consumidor(file_name)
        # Eliminem el fitxer.
        os.remove(file_name)
        messages.add_message(request, messages.INFO, request.FILES['csv_file'].name)

    return redirect('/atelier/consumidor')


# Pedidos

@staff_member_required
def pedido_to_csv_form(request):
    if request.user.is_superuser:
        return csv_form(request, '/atelier/pedido-import-from-csv/', 'Pedido')          
    else:
        return HttpResponseBadRequest('Error 404')

@staff_member_required
def pedido_import_from_csv(request):
    if request.user.is_superuser:
        # Guardem el fitxer a disc
        file_name = handle_uploaded_file(request.FILES['csv_file'])
        # Importem les dades del fitxer csv
        import_csv_pedido(file_name)
        # Eliminem el fitxer.
        os.remove(file_name)
        messages.add_message(request, messages.INFO, request.FILES['csv_file'].name)

    return redirect('/atelier/consumidor')

# Gastos

@staff_member_required
def gastos_from_csv_form(request):
    if request.user.is_superuser:
        form = ImportGastosFromCSV()
        context = {
            'form':form,
            'action': '/atelier/gastos-import-from-csv/',
            'url_destination': '/',
            'titol': 'Importar CSV',
            'descripcio':'Importar %s desde un fichero en formato CSV.' % 'Gastos'
        }
        return render(request, 'atelier/pcr_form_p.html', context)  

    return redirect('/atelier/gasto')


@staff_member_required
def gastos_import_from_csv(request):
    # @user_passes_test(lambda u: u.is_superuser)
    if request.user.is_superuser:
        ejercicio = request.POST.get('ejercicio')
        mes = request.POST.get('mes')
        ejercicio_obj = get_object_or_404(Ejercicio, pk=ejercicio)
        # Guardem el fitxer a disc
        file_name = handle_uploaded_file(request.FILES['csv_file'])
        # Importem les dades del fitxer csv
        import_csv_gasto(file_name, ejercicio_obj, mes)
        # Eliminem el fitxer.
        os.remove(file_name)
        #messages.add_message(request, messages.INFO, request.FILES['csv_file'].name)

    return redirect('/atelier/gasto')


##################################
# INFORME: Ventes entre dos anys #
##################################

@staff_member_required
def sales_compare_years_report(request):
    """
        L'usuari dona dos anys. Es vol veure els números des del Setembre dels anys
        introduïts fins a l'Agost del seu any seguent per fer una comparativa més a
        més entre els dos anys seleccionats per l'usuari. Es vol veure el total
        mensual, acomulat mensual, la diferència entre els dos mateixos mesos dels 
        dos anys donats i la diferència del seu acomulat mensual. Sis columnes.
        Cada fila del llistat corespon a un més.
    """
    year1 = int(request.POST.get('year1', ''))
    year2 = int(request.POST.get('year2', ''))
    list1 = []
    list1_str = []
    list2 = []
    list2_str = []
    acumul1 = []
    acumul1_str = []
    acumul2 = []
    acumul2_str = []
    ac1 = 0
    ac2 = 0
    dif_list = []
    dif_acumul = []
    month_str=['Setiembre', 'Octubre', 'Noviembre', 'Diciembre', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto']
    months = ['09', '10', '11', '12', '01', '02', '03', '04', '05', '06', '07', '08', '09']
    month_years = []

    for i,month in enumerate(months[:-1]):
        # Calculem la columna de mesos amb els anys implicats
        month_years.append( '<b>{}(</b> {}, <span style="color:#888">{}</span><b>)</b> '.format(month_str[i], year1, year2)  )   

        # Calculem les dates inicial i final per a cada més dels dos anys a comparar
        init_date_1 = '{}-{}-01 00:00:00'.format(year1, month)
        init_date_2 = '{}-{}-01 00:00:00'.format(year2, month)        
        if i == 3:
            year1 += 1
            year2 += 1
        end_date_1 = '{}-{}-01 00:00:00'.format(year1, months[i + 1])
        end_date_2 = '{}-{}-01 00:00:00'.format(year2, months[i + 1])
        print(init_date_1, end_date_1, init_date_2, end_date_2)

        # Passem a tipus datetime
        id1 = parse_datetime(init_date_1) # datetime.strptime(init_date_1, '%d/%m/%Y')
        ed1 = parse_datetime(end_date_1) # datetime.strptime(end_date_1, '%d/%m/%Y')
        ed1 = ed1 - timedelta(days=1)
        id2 = parse_datetime(init_date_2) # datetime.strptime(init_date_1, '%d/%m/%Y')
        ed2 = parse_datetime(end_date_2) # datetime.strptime(end_date_1, '%d/%m/%Y')
        ed2 = ed2 - timedelta(days=1)

        print(id1, ed1)

        # Consultem la suma mensual i l'afegim a les llistes segons l'any
        sum1 = Articulo.objects.filter( pedido__dia__range=(id1, ed1)).aggregate(total=Sum('importe'))
        sum2 = Articulo.objects.filter( pedido__dia__range=(id2, ed2)).aggregate(total=Sum('importe'))
        print(sum1,sum2)

        if sum1['total'] is not None:
            # '{:,.2f} €'.format(sum1['total'])
            list1_str.append('{:,.2f} €'.format(sum1['total']))
            list1.append(sum1['total'])
            ac1 += sum1['total']
        else:
            list1_str.append('{:,.2f} €'.format(0))
            list1.append(0)

        if sum2['total'] is not None:
            list2_str.append('<span style="color:#888">{:,.2f} €</span>'.format(sum2['total']))
            ac2 += sum2['total']
            list2.append(sum2['total'])
        else:
            list2_str.append('<span style="color:#888">{:,.2f} €</span>'.format(0))            
            list2.append(0)

        # Acumulats
        acumul1.append(ac1)
        acumul1_str.append('{:,.2f} €'.format(ac1))
        acumul2.append(ac2)
        acumul2_str.append('<span style="color:#888">{:,.2f} €</span>'.format(ac2))
        dif_list.append( getCurrencyHtml(list1[-1] - list2[-1]) )
        dif_acumul.append( getCurrencyHtml(acumul1[-1] - acumul2[-1]) )
    context = {
        'year1': year1 - 1,
        'year2': year2 - 1,
        'month_years': month_years,
        'list1': list1_str,
        'list2': list2_str,
        'acumul1': acumul1_str,
        'acumul2': acumul2_str,
        'dif_list': dif_list,
        'dif_acumul': dif_acumul,
        'action': '/atelier/pedido/', 
        'titol': 'Comparativa de ventas',
        'descripcio':'Comparacion de ventas entre {} i {}'.format(year1, year2),   
    }
    return render(request, 'atelier/sales_compare_years.html', context)


#################################################################################
# PDF: vista per mostrar el formulari genèric per poder descarregar fitxers PDF #
#################################################################################

def get_pdf_form_view(request, action, titol, files, url_destination):
    context = { 
        'static_files': files,  #['bobines.pdf',],
        'action': action,
        'url_destination': url_destination, #'/materials/solicitudsdematerial/',
        'titol': titol + ' - Informe en formato PDF o CSV',
        'descripcio':'Imprime o guarda el PDF o CSV'}
    return render(request, 'atelier/pcr_form_p.html', context)


################################
# VISTA PER IMPRIMIR UN PEDIDO #
################################

def pdf_pedido(request, pk):
    if not request.user.has_perm('atelier.view_pedido'):
        return redirect('/')
    file_names_list = []
    pedido = Pedido.objects.get(pk=pk)
    file_names_list.append(print_order(pedido))
    names_only_list = ['pdf/' + s.split('/')[-1] for s in file_names_list]
    return get_pdf_form_view(request, action='/atelier/pedido/', titol='Pedidos', files=names_only_list, url_destination='/atelier/pedido/')


def pdf_pedido_pagos(request, pk):
    if not request.user.has_perm('atelier.view_pago'):
        return redirect('/')
    pedido = Pedido.objects.get(pk=pk)
    file = 'pdf/' + print_order_payments(pedido)
    return get_pdf_form_view(request, action='/atelier/pedido/', titol='Pagos de un Pedido', files=[file,], url_destination='/atelier/pedido/')
 


##########################################
# REGULARIZAR PAGOS CON RECIBO ENTREGADO #
##########################################

def regularizar_pagos_view(request):
    pagos_count = 0
    pagos_nocaja_count = 0
    for pedido in Pedido.objects.all():
        if pedido.pendiente() <= 0:
            # pagos
            for pago in pedido.pagos.all():
                pago.recibo_creado = True
                pago.save()
                pagos_count += 1
            # pagos no caja
            for pago in pedido.pagos_no_caja.all():
                pago.recibo_creado = True
                pago.save()
                pagos_nocaja_count += 1
                if not pedido.iva:
                    pedido.iva = True
                    pedido.save()

    messages.add_message(request, messages.INFO, f"Se han regularizado {pagos_count} pagos y {pagos_nocaja_count} pagos no a caja.")
    return redirect('/atelier/pedido/')



###############################
# GASTOS: GENERAR FACTURACIÓN #
###############################

def gastos_generar_facturacion_view(request):
    if request.user.is_superuser:
        # Formulari 
        if request.method == 'GET':
            form = GastosGenerarFacturacionForm()
            context = {
                'form':form,
                'action': request.path,
                'url_destination': '/',
                'titol': 'Generar Facturación',
                'descripcio':'Crea entradas para: FACTURACIÓN (+IVA), COSTE e IVA según los Pedidos de un ejercicio seleccionado.'
            }
            return render(request, 'atelier/pcr_form_p.html', context)
        
        # POST
        ejercicio_id = request.POST.get('ejercicio')
        ejercicio = get_object_or_404(Ejercicio, pk=ejercicio_id)
        # Calcular valors
        #pedidos_iva = Pedido.objects.filter(ejercicio=ejercicio)
        
        messages.add_message(request, messages.INFO, f"0 Entradas creadas en el ejercicio: {ejercicio}")

    return redirect('/atelier/gasto')
