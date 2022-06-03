#-*- coding: utf-8 -*-
import os
import random
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from tr.settings import BASE_DIR

PDF_PATH = os.path.join(BASE_DIR, 'static/pdf/')

MARGIN_X = 50
MARGIN_X_RIGHT = 550

# HELPERS: ########################################################

def draw_line(canvas, x, y, x_to, y_to):
    p = canvas.beginPath()
    p.moveTo(x, y)
    p.lineTo(x_to, y_to)
    p.close()
    canvas.drawPath(p)


def xstr(s):
    if s is None:
        return ''
    return str(s)


def text_bold(c, x, y, string):
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, string)
    c.setFont("Helvetica", 12)


def field(c, x, y, label, string):
    """ Per imprimir un camp amb etiqueta amb negreta """
    text_bold(c, x, y, label)
    text_len = c.stringWidth(label, "Helvetica-Bold", 12) + 10
    c.drawString(x + text_len, y, xstr(string))

def fieldr(c, x, y, label, string):
    """ Per imprimir un camp amb etiqueta amb negreta, alineat a la dreta del punt x """
    # primer el string
    string_len = c.stringWidth(string, "Helvetica", 12)
    x -= string_len
    c.drawString(x, y, xstr(string))
    # Ara el label
    margin = 10
    if string == "":
        margin = 0
    label_len = c.stringWidth(label, "Helvetica-Bold", 12) + margin
    x -= label_len
    text_bold(c, x, y, label)


def textarea(c, text, x, y, lineY, max_lines):
    variacions_lines = text.split('\r')
    topY = y
    lines_in_variacions = max_lines + 1
    for line in variacions_lines:     
        # Línies en blank
        if line == '\n':
            topY -= lineY
            lines_in_variacions -= 1
            if lines_in_variacions == 1:
                break
        # Línies             
        words = line.split()
        line_from_words = ""
        for word in words:
            if len(line_from_words) + len(word) < 97:
                line_from_words += word + ' '
            else:
                # Pintem les línies que ocupen tot l'espai
                c.drawString(MARGIN_X + 10,topY, line_from_words[:-1])
                topY -= lineY
                line_from_words = ""
                lines_in_variacions -= 1
                if lines_in_variacions == 1:
                    break
        # Pintem línies pendents que no ocupen tot l'espai
        if line_from_words != "":
            c.drawString(MARGIN_X + 10,topY, line_from_words)
            topY -= lineY
            lines_in_variacions -= 1
            if lines_in_variacions == 1:
                break
        # Si ja hem pintat el màxim número de línies sortim
        if lines_in_variacions == 1:
            break        
    return topY - (lineY + lineY * lines_in_variacions)


def textareaV2(c, text, x, y, lineY, max_lines, max_width):
    topY = y
    lines = []
    line = ''
    # Creem les línies segons el tamany màxim
    for char in text:
        if char == '\r':
            continue
        if char == '\n':
            lines.append(line)
            line = ''
            continue
        actual_width = c.stringWidth(line + char, "Helvetica", 12)
        if actual_width > max_width:
            if char != ' ' and line[-1] != ' ':
                line += '-'
            lines.append(line)
            line = ''
        line += char
    lines.append(line)

    # Imprimim les línies
    for line in lines:
        c.drawString(MARGIN_X + 10, topY, line)
        topY -= lineY
        max_lines -= 1
        if max_lines == 0:
            break



# REPORT: PEDIDOS ########################################################
# A4 595 x 842 pixels a 72 PPI
def print_order_report(orders):
    file_names = []
    for order in orders:
        file_names.append( print_order(order) )
    return file_names


def print_order(order):
    topY = 800; lineY = 15
    file_name = PDF_PATH + "order_{}.pdf".format(order.pk)
    c = canvas.Canvas(file_name)

    # Fecha / Fecha Entrega
    field(c, MARGIN_X, topY, "Fecha:", order.dia_pedido.strftime('%d/%m/%Y'))
    field(c, MARGIN_X + 140, topY, "ID:", f"NP{order.pk}-EX{random.randint(100,200)}")
    field(c, MARGIN_X + 310, topY,"Fecha entrega:", order.dia_entrega.strftime('%d/%m/%Y'))
    topY -= lineY

    # Line
    draw_line(c, MARGIN_X, topY, MARGIN_X_RIGHT, topY)
    topY -= lineY

    # BOUTIQUE / CLIENTE
    field(c, MARGIN_X, topY, "BOUTIQUE:", "Atelier")
    field(c, MARGIN_X + 210, topY, "CLIENTE:", order.consumidor.nombre)
    topY -= lineY

    # Round rect
    c.roundRect(MARGIN_X, topY, 500, lineY * -2, 0, stroke=1, fill=0)
    topY -= lineY * 1.5

    # MODELO / SERIE / COLOR / TALLA
    field(c, MARGIN_X + 10,topY,"MODELO", "")
    field(c, MARGIN_X + 210,topY,"SERIE", "")
    field(c, MARGIN_X + 310,topY,"COLOR", "")
    field(c, MARGIN_X + 410,topY,"TALLA", "")
    topY -= lineY * 2

    for articulo in order.articulos.all():
        field(c, MARGIN_X + 0, topY, "", articulo.desc)
        field(c, MARGIN_X + 200, topY, "", articulo.serie)
        field(c, MARGIN_X + 300, topY, "", articulo.color)
        field(c, MARGIN_X + 400, topY, "", articulo.talla)
        # fieldr(c, MARGIN_X + 352.5, topY, "", '{:,.2f} €'.format(articulo.importe) )
        topY -= lineY  

    # Round rect
    c.roundRect(MARGIN_X, topY, 500, -350, 0, stroke=1, fill=0)
    topY -= lineY * 1.5

    # VARIACIONES
    text_bold(c, MARGIN_X + 10,topY,"VARIACIONES:")
    topY -= lineY
    #c.setFont("Helvetica", 10)
    #topY = textarea(c, order.variaciones, x=MARGIN_X + 10, y=topY, lineY=lineY, max_lines=20)
    #c.setFont("Helvetica", 12)
    max_lines = 20
    textareaV2(c, order.variaciones, x=MARGIN_X + 10,  y=topY, lineY=lineY, max_lines=20, max_width=MARGIN_X_RIGHT - 70)
    topY -= max_lines * lineY + lineY * 3

    field(c, MARGIN_X + 10, topY,  "Contorno pecho total.....:", xstr(order.contorno_pecho_total))
    field(c, MARGIN_X + 250, topY, "Contorno cintura........:",xstr(order.contorno_cintura))
    topY -= lineY 
    field(c, MARGIN_X + 10, topY,  "Contorno cadera.............:", xstr(order.contorno_cadera))
    field(c, MARGIN_X + 250, topY, "Largo talle delante......:", xstr(order.largo_talle_delante))
    topY -= lineY 
    field(c, MARGIN_X + 10, topY,  "Largo talle espalda.........:", xstr(order.largo_talle_espalda))
    field(c, MARGIN_X + 250, topY, "Largo falda..................:", xstr(order.largo_falda))
    topY -= lineY 
    field(c, MARGIN_X + 10, topY,  "Largo chaqueta delante.:", xstr(order.largo_chaqueta_delante))
    field(c, MARGIN_X + 250, topY, "Largo blusa delante....:", xstr(order.largo_blusa_delante))
    topY -= lineY 
    field(c, MARGIN_X + 10, topY,  "Largo manga chaqueta..:", xstr(order.largo_manga_chaqueta))
    field(c, MARGIN_X + 250, topY, "Largo manga blusa.....:", xstr(order.largo_manga_blusa))
    topY -= lineY 
    field(c, MARGIN_X + 10, topY,  "Contorno brazo...............:", xstr(order.contorno_brazo))
    field(c, MARGIN_X + 250, topY, "De hombro a hombro..:", xstr(order.de_hombro_a_hombro))
    # topY -= lineY 

    c.showPage()
    c.save()
    return file_name


# REPORT: PAGOS ########################################################
# A4 595 x 842 pixels a 72 PPI
def print_order_payments(order):
    print('print_order_payments...')
    topY = 800; lineY = 15
    file_name = PDF_PATH + "order_payments_{}.pdf".format(order.pk)
    c = canvas.Canvas(file_name)

    # TERESA RIPOLL atelier
    field(c, MARGIN_X, topY, "TERESA RIPOLL", "Atelier")
    topY -= lineY
    c.drawString(MARGIN_X, topY, "C/ Corcega 288 principal 1")
    topY -= lineY
    c.drawString(MARGIN_X, topY, "08008 Barcelona")
    topY -= lineY
    field(c, MARGIN_X, topY,"Tel.", "93 676 79 27")
    topY -= lineY * 1.5

    # PRIMERA FILA
    c.roundRect(MARGIN_X, topY, 250, lineY * -2, 0, stroke=1, fill=0)
    c.roundRect(MARGIN_X + 250, topY, 150, lineY * -2, 0, stroke=1, fill=0)
    c.roundRect(MARGIN_X + 400, topY, 75, lineY * -2, 0, stroke=1, fill=0)
    topY -= lineY * 1.2
    field(c, MARGIN_X + 10, topY, "FICHA:", "clienta modelo, pagos seguimiento")
    field(c, MARGIN_X + 260, topY, "Fecha:", order.dia.strftime('%d/%m/%Y'))
    field(c, MARGIN_X + 410, topY, "Nº:", order.pk)
    topY -= lineY - (lineY * 0.2)

    # SEGONA FILA
    c.roundRect(MARGIN_X, topY, 475, lineY * -6, 0, stroke=1, fill=0)
    topY -= lineY * 1.2
    text_bold(c, MARGIN_X + 10, topY, order.consumidor.nombre)
    field(c, MARGIN_X + 260, topY, "Tel.:", order.consumidor.telefono)
    topY -= lineY 
    text_bold(c, MARGIN_X + 10,topY,"Dirección:")
    text_bold(c, MARGIN_X + 260,topY,"Fecha del evento:")
    topY -= lineY 
    c.drawString(MARGIN_X + 260, topY, str(order.dia_evento))
    topY = textarea(c, order.consumidor.direccion, x=MARGIN_X + 10, y=topY, lineY=lineY, max_lines=3) + (lineY * 2.2)

    # TERCERA FILA
    c.roundRect(MARGIN_X, topY, 250, lineY * -2, 0, stroke=1, fill=0)
    c.roundRect(MARGIN_X + 250, topY, 225, lineY * -2, 0, stroke=1, fill=0)
    topY -= lineY * 1.2
    field(c, MARGIN_X + 10, topY, "Email:", order.consumidor.email)
    field(c, MARGIN_X + 260, topY, "Lugar evento:", order.lugar_evento)
    topY -= lineY - (lineY * 0.2)

    # QUARTA FILA
    # c.roundRect(MARGIN_X, topY, 475, lineY * -2, 0, stroke=1, fill=0)
    # topY -= lineY * 1.2
    #field(c, MARGIN_X + 10, topY, "Serie:", order.serie)
    #field(c, MARGIN_X + 260, topY, "Color:", order.color)
    #field(c, MARGIN_X + 400, topY, "T.", order.talla)
    topY -= lineY * 2

    # ARTICLES
    text_bold(c, MARGIN_X, topY, "ARTÍCULOS:")
    topY -= lineY * 0.5
    c.roundRect(MARGIN_X, topY, 375, lineY * -2, 0, stroke=1, fill=0)
    c.roundRect(MARGIN_X + 375, topY, 100, lineY * -2, 0, stroke=1, fill=0)
    topY -= lineY * 1.2
    field(c, MARGIN_X + 10, topY, "ARTÍCULO", "")
    text_bold(c, MARGIN_X + 385, topY, "PRECIO")
    topY -= lineY * 2 - (lineY * 0.2)

    for articulo in order.articulos.all():
        # Calcular text de l'article
        serie = ""
        if articulo.serie != "" and articulo.serie is not None:
            serie = "S." + articulo.serie
        color = ""
        if articulo.color != "" and articulo.color is not None:
            color = "C." + articulo.color
        talla = ""
        if articulo.talla != "--":
            talla = "T." + articulo.get_talla_display()
        articulo_det = "{} {} {} {}".format(articulo.desc, serie, color, talla)
        field(c, MARGIN_X + 10, topY, "", articulo_det)
        # Import
        fieldr(c, MARGIN_X + 465, topY, "", '{:,.2f} €'.format(articulo.importe) )
        topY -= lineY  

    c.roundRect(MARGIN_X, topY, 475, lineY * -2, 0, stroke=1, fill=0)
    topY -= lineY * 1.2
    fieldr(c, MARGIN_X + 465, topY, "Importe total:", '{:,.2f} €'.format(order.importe_total()) )    
    topY -= lineY * 3 # - (lineY * 0.2)

    # PAGAMENTS EFECTIU
    text_bold(c, MARGIN_X, topY, "PAGOS EFECTIVO:")
    topY -= lineY * 0.5
    c.roundRect(MARGIN_X, topY, 250, lineY * -2, 0, stroke=1, fill=0)
    c.roundRect(MARGIN_X + 250, topY, 112.5, lineY * -2, 0, stroke=1, fill=0)
    c.roundRect(MARGIN_X + 362.5, topY, 112.5, lineY * -2, 0, stroke=1, fill=0)
    topY -= lineY * 1.2
    fieldr(c, MARGIN_X + 240, topY, "Descripción", "")
    text_bold(c, MARGIN_X + 260, topY, "Precio")
    text_bold(c, MARGIN_X + 372.5, topY, "Forma Pago")
    topY -= lineY * 2 - (lineY * 0.2)

    for pago in order.pagos.all():
        field(c, MARGIN_X + 10, topY, pago.dia.strftime('%d/%m/%Y'), pago.desc)
        fieldr(c, MARGIN_X + 352.5, topY, "", '{:,.2f} €'.format(pago.importe) )
        c.drawString(MARGIN_X + 372.5, topY, "EFECTIVO")
        pago.recibo_creado = True
        pago.save()
        topY -= lineY

    for pago in order.pagos_no_caja.all():
        field(c, MARGIN_X + 10, topY, pago.dia.strftime('%d/%m/%Y'), pago.desc)
        fieldr(c, MARGIN_X + 352.5, topY, "", '{:,.2f} €'.format(pago.importe) )
        c.drawString(MARGIN_X + 372.5, topY, pago.get_forma_pago_display())
        pago.recibo_creado = True
        pago.save()
        if not pago.pedido.iva:
            pago.pedido.iva = True
            pago.pedido.save()
        topY -= lineY

    c.roundRect(MARGIN_X, topY, 250, lineY * -2, 0, stroke=1, fill=0)
    c.roundRect(MARGIN_X + 250, topY, 225, lineY * -2, 0, stroke=1, fill=0)
    topY -= lineY * 1.2
    field(c, MARGIN_X + 10, topY, "Pendiente:", '{:,.2f} €'.format(order.pendiente()) )
    field(c, MARGIN_X + 260, topY, "Total pagado:", '{:,.2f} €'.format(order.total_pagado()) )

    c.showPage()
    c.save()

    return "order_payments_{}.pdf".format(order.pk)
    

