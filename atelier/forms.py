#-*- coding: utf-8 -*-
from django import forms
from django.utils.timezone import now

from .models import Ejercicio

class DateInput(forms.DateInput):
    input_type = 'date'


class SalesCompareYearsForm(forms.Form):
    date = now()
    year1 = forms.IntegerField(label="Primer año", required=True, initial=date.year)
    year2 = forms.IntegerField(label="Segundo año", required=True, initial=date.year - 1)


class GetCSVFileForm(forms.Form):
    csv_file = forms.FileField(label="Selecciona un fitxero en formato CSV")


class ImportGastosFromCSV(forms.Form):
    ejercicio = forms.ChoiceField(choices=[(f"{ejercicio.pk}", ejercicio.nombre) for ejercicio in Ejercicio.objects.all()])
    mes = forms.ChoiceField(choices=[
        ("setiembre", "Setiembre"),
        ("octubre", "Octubre"),
        ("noviembre", "Noviembre"),
        ("diciembre", "Diciembre"),
        ("enero", "Enero"),
        ("febrero", "Febrero"),
        ("marzo", "Marzo"),
        ("abril", "Abril"),
        ("mayo", "Mayo"),
        ("junio", "Junio"),
        ("julio", "Julio"),
        ("agosto", "Agosto"),
    ])
    csv_file = forms.FileField(label="CSV -> Sin cabeceras, solo con los datos a cargar")
