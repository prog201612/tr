#-*- coding: utf-8 -*-
import os
from datetime import timedelta

from django.utils.dateparse import parse_datetime
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.contrib import messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseBadRequest

from tr.settings import BASE_DIR
from .forms import SalesCompareYearsForm, GetCSVFileForm
from .models import Articulo
from .helpers import handle_uploaded_file, import_csv_consumidor, import_csv_pedido, \
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


##################################
# INFORME: Ventes entre dos anys #
##################################

@staff_member_required
def sales_compare_years(request):
    form = SalesCompareYearsForm()
    context = {
        'form':form,
        'action': '/atelier/sales-compare-years-report/',
        'url_destination': '/atelier/pedido/',
        'titol': 'Comparativa de ventas',
        'descripcio':'Comparacion de ventas de Febrero a Agosto, entre dos anyos.'
    }
    return render(request, 'atelier/pcr_form_p.html', context)

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
        # Calculem la columna de mesos amb els anys implicats
        month_years.append( '<b>{}(</b> {}, <span style="color:#888">{}</span><b>)</b> '.format(month_str[i], year1, year2)  )   
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
