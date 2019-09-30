#-*- coding: utf-8 -*-
from django import forms
from django.utils.timezone import now

class DateInput(forms.DateInput):
    input_type = 'date'


class SalesCompareYearsForm(forms.Form):
    date = now()
    year1 = forms.IntegerField(label="Primer año", required=True, initial=date.year)
    year2 = forms.IntegerField(label="Segundo año", required=True, initial=date.year - 1)


class GetCSVFileForm(forms.Form):
    csv_file = forms.FileField(label="Selecciona un fitxero en formato CSV")
