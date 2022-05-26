from django.utils.html import format_html

def get_currency_representation(value, positive_color='green', negative_color='red'): 
    """
    Columna de llistat al Admin de django a les caixes per veure el saldo 
    anterior en verd si és positiu o vermell si és negatiu.
    """
    if value == 0:
        return " "
    color = positive_color
    if value < 0:
        color = negative_color
    return format_html(
        '<span style="color:{};text-align:right;width:100%;display:inline-block;">{}</span>', color, '{:0,.2f}'.format(value)) #  €

