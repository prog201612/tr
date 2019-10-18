#-*- coding: utf-8 -*-
import decimal
from functools import reduce
import datetime

from django.db import models
from django.utils.timezone import now
from django.core.validators import BaseValidator
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db.models import Sum

# Create your models here.


########
# Caja #
########

# HELPER

def get_week_by_date(date):
    """ Retorna el número de setmana donada una data """
    return int( date.strftime("%V") )

def week_in_year(year, week):
    try:
        d = "{}-W{}".format(year, week)
        datetime.datetime.strptime(d + '-1', "%G-W%V-%u")
        return True
    except:
        return False
 

# DEFAULT VALUE FUNCTIONS

def get_week_by_now():
    """ Retorna el número de setmana segons avui """
    now = datetime.datetime.now()
    return int( now.strftime("%V") )

def get_year_by_now():
    """ Retorna l'any segons avui """
    return datetime.datetime.now().year

# VALIDATORS

def week_validator(value):
    """
        Funció validadora de camp. Donat un enter valida si a l'any
        actual existeix aquell número de setmana
    """
    # get year
    year = datetime.datetime.now().year
    # validata week on year
    if not week_in_year(year, value):
        raise ValidationError(
            '%(value)s is not a valid week number for %(year)s.',
            params={'value': value, 'year': year},
        )

# CAJA 

class Caja(models.Model):
    year = models.IntegerField(verbose_name="Año", default=get_year_by_now())
    semana = models.IntegerField(default=get_week_by_now(), validators=[week_validator])
    saldo_anterior = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    saldo_cierre = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    cerrada = models.BooleanField(default=False)
    caja_siguiente = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='caja_anterior')

    created = models.DateTimeField(auto_now_add=True) # només al crear , 
    updated = models.DateTimeField(auto_now=True) # cada modificació auto_now=True, 

    def __str__(self):
        return "{} - {}".format( self.year, self.semana )

    def get_monday_by_week(self):
        ''' Partint de l'any actual i el número de setmana del registre actual, calculem
            el datetime.date corresponent al dilluns d'aquella setmana '''
        if self.semana:
            # year = datetime.datetime.now().year
            d = "{}-W{}".format(self.year, self.semana)
            return datetime.datetime.strptime(d + '-1', "%G-W%V-%u").date()

    # LINKS

    def caja_anterior_link(self):
        """ 
            Per tenir un link d'accés a la caixa anterior des de la pantalla de
            l'admin per editar una caixa.
        """
        cajas = self.caja_anterior.all()
        if len(cajas) > 0:
            return format_html(
                '<a href="/atelier/caja/{}/change/">Caja Anterior</a>', cajas[0].pk)
        return ""

    def caja_siguiente_link(self):
        """ 
            Per tenir un link d'accés a la caixa següent des de la pantalla de
            l'admin per editar una caixa.
        """
        if self.caja_siguiente is not None:
            return format_html(
                '<a href="/atelier/caja/{}/change/">Caja Siguiente</a>', self.caja_siguiente.pk)
        return ""

    # TOTALS

    def get_total_apuntes_entrada(self):
        """
            Fa un sumatori de tots els apunts d'entrada relacionats a la caixa actual
        """
        total_entrada_tuple = self.apuntes.all().aggregate(total_entrada=Sum('entrada'))
        if total_entrada_tuple['total_entrada']:
            return total_entrada_tuple['total_entrada']
        return 0
    get_total_apuntes_entrada.short_description="Total apuntes entrada"

    def get_total_apuntes_entrada_str(self):
        return '{:0,.2f} €'.format(self.get_total_apuntes_entrada())


    def get_total_apuntes_salida(self):
        """
            Fa un sumatori de tots els apunts de sortida relacionats a la caixa actual
        """
        total_salida_tuple = self.apuntes.all().aggregate(total_salida=Sum('salida'))
        if total_salida_tuple['total_salida']:
            return total_salida_tuple['total_salida']
        return 0
    get_total_apuntes_salida.short_description="Total apuntes salida"

    def get_total_apuntes_salida_str(self):
        return '{:0,.2f} €'.format(self.get_total_apuntes_salida())


    def get_total_pagos(self):
        """
            Fa un sumatori de tots els pagaments en efectiu relacionats amb una caixa.
        """
        total_pagos = self.pagos.all().aggregate(total_pagos=Sum('importe'))
        if total_pagos['total_pagos']:
            return total_pagos['total_pagos']
        return 0
    get_total_pagos.short_description="Total pagos"

    def get_total_pagos_str(self):
        return '{:0,.2f} €'.format(self.get_total_pagos())    


    def get_saldo_cierre(self):
        """
            De la caixa actual, agafa el seu saldo anterior (implica haver tancat la
            caixa anterior) se li suma els pagaments en efectiu, els apunts d'entrada
            i s'hi resta els apunts de sortida.
        """
        return self.saldo_anterior + self.get_total_apuntes_entrada() + self.get_total_pagos() - self.get_total_apuntes_salida()
    get_saldo_cierre.short_description="Saldo cierre"

    def get_saldo_cierre_str(self):
        return '{:0,.2f} €'.format(self.get_saldo_cierre())  


    def get_provisional_saldo_anterior(self):
        ''' Mirem si hi ha caixa anterior. Si no hi és no hi ha saldo anterior.
            Si hi ha caixa anterior i no està tancada acumulem el total de pagaments
            mes el total d'apunts d'entrada menys el total d'aputs de sortida. Si la
            caixa anterior està tancada n'agafem el saldo de tancament. '''
        saldo = 0
        # caja_anterior: contindrà la última caixa o Null
        caja_anterior = self.caja_anterior.all().first()
        print(caja_anterior)
        while caja_anterior != None and not caja_anterior.cerrada:
            saldo += caja_anterior.get_total_pagos() + caja_anterior.get_total_apuntes_entrada() + caja_anterior.get_total_apuntes_salida()
            # Preparem les següents dades del bucle
            caja_anterior = caja_anterior.caja_anterior.all().first()
        # si hi ha caixa tencada hi somem el saldo de cierre
        if caja_anterior != None and caja_anterior.cerrada:
            saldo += caja_anterior.saldo_cierre
        return saldo
    get_provisional_saldo_anterior.short_description="Saldo anterior provisional"

    def get_provisional_saldo_anterior_str(self):
        return '{:0,.2f} €'.format(self.get_provisional_saldo_anterior())


    def get_provisional_saldo(self):
        """
            Utilitzant la funció anterior calcula un saldo provisional o no tant 
            provisional, depenent de si la caixa anterior està oberta o tancada i
            a aquest saldo li suma el total de pagaments i apunts d'entrada de la
            caixa actual i li resta els apunts de sortida també d'aquesta.
        """
        return self.get_provisional_saldo_anterior() + self.get_total_pagos() + self.get_total_apuntes_entrada() - self.get_total_apuntes_salida()
    get_provisional_saldo.short_description="Saldo provisional"

    def get_provisional_saldo_str(self):
        return '{:0,.2f} €'.format(self.get_provisional_saldo())

    # LIST COLUMN RIGHT ALIGN

    def saldo_anterior_(self): 
        """
            Columna de llistat al Admin de django a les caixes per veure el saldo 
            anterior en verd si és positiu o vermell si és negatiu.
        """
        color = 'green'
        if self.saldo_anterior < 0:
            color = 'red'
        return format_html(
            '<span style="color:{};text-align:right;width:100%;display:inline-block;">{}</span>', color, '{:0,.2f} €'.format(self.saldo_anterior))

    def saldo_cierre_(self): 
        """
            Columna de llistat al Admin de django a les caixes per veure el saldo 
            de tancament en verd si és positiu o vermell si és negatiu.
        """        
        color = 'green'
        if self.saldo_cierre < 0:
            color = 'red'
        return format_html(
            '<span style="color:{};text-align:right;width:100%;display:inline-block;">{}</span>', color, '{:0,.2f} €'.format(self.saldo_cierre))


    # META

    class Meta:
        """
            Ordenem les caixes per any i número de setmana de més actual a menys
        """
        ordering = ['-year', '-semana']


# SIGNALS

@receiver(post_save, sender=Caja)
def ensure_link_caja_anterior(sender, instance, **kwargs):
    ''' 
        Quan es crea una caixa es busca la que no te caja_siguiente i es crea l'enllaç.
        Si hi ha setmanes intermitges entre l'actual a crear i la caixà que no té
        caja_siguiente, es creen. No hi ha cap bucle ja que al crear la caixa anterior
        es tornarà a cridar aquest mètode una altra vegada. D'aquesta manera s'anirà
        creant caixes anteriors fins a arribar a contactar amb la que era la última de 
        la llista.
    '''
    # La caixa que estem creant actualment també surtirà al filtre agafem la d'abans d'aquesta
    caja_anterior = Caja.objects.filter(caja_siguiente=None).order_by('year','semana').first()
    print(caja_anterior)
    if caja_anterior:
        # any1 < any2, semana1 < semana2 si any1 == any2.
        any1 = caja_anterior.year
        semana1 = caja_anterior.semana
        any2 = instance.year
        semana2 = instance.semana

        # Si és la setmana seguent creem l'enllaç i sortim
        if (any1 == any2 and semana1 + 1 == semana2):
            caja_anterior.caja_siguiente = instance
            caja_anterior.save()
            return

        # Si no hem arrivat a la caja anterior, creem l'anterior a la instància actual anllaçant-la amb aquesta
        print(any1, any2, int("{}{:02d}".format(any1, semana1)), (int(f"{any2}{semana2}") - 1) )
        print( int(any1) <= int(any2) and int(f"{any1}{semana1}") < int("{}{:02d}".format(any2, semana2)) - 1)
        if int(any1) <= int(any2) and int("{}{:02d}".format(any1, semana1)) < int("{}{:02d}".format(any2, semana2)) - 1:
            semana2 -= 1
            # Si arrivem a la setmana zero, començem desde l'última setmana de l'any anterior
            if semana2 == 0:
                semana2 = 52
                any2 -=1
            # Creem la caixa anterior a la actual.
            new = Caja(year=any2, semana=semana2, caja_siguiente=instance)
            new.save()


###########
# Apuntes #
###########

# APUNTES

class Apuntes(models.Model):
    caja = models.ForeignKey('Caja', on_delete=models.CASCADE, related_name='apuntes')
    dia = models.DateField(default=now)
    concepto = models.CharField(verbose_name="Descripción", max_length=100)
    entrada = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    salida = models.DecimalField(max_digits=9, decimal_places=2, default=0)

    created = models.DateTimeField(auto_now_add=True) # només al crear
    updated = models.DateTimeField(auto_now=True) # cada modificació


##############
# Consumidor #
##############

class Consumidor(models.Model):
    nombre = models.CharField(max_length=50)
    telefono = models.CharField(verbose_name="Teléfono", max_length=15, null=True, blank=True)
    direccion = models.TextField(verbose_name="Dirección", null=True, blank=True)
    email = models.CharField(max_length=50, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True) # només al crear
    updated = models.DateTimeField(auto_now=True) # cada modificació

    def __str__(self):
        return self.nombre

##########
# Pedido #
##########

NOS_CONOCIO = (
    (1, 'POR OTRA CLIENTA'),
    (2, 'POR WEB'),
    (3, 'POR INSTAGRAM'),
    (4, 'POR FACEBOOK'),
    (5, 'YA ES CLIENTA'),
    (6, 'OTROS'),
)

TALLAS = (
    ('--', '--'),  
    ('ME', 'MEDIDA'),
    ('38', '38'),
    ('40', '40'),
    ('42', '42'),
    ('44', '44'),
    ('46', '46'),
    ('48', '48'),
    ('50', '50'),
    ('52', '52'),
    ('54', '54'),
    ('56', '56'),
    ('58', '58'),
    ('60', '60'),
    ('62', '62'),
    ('64', '64'),
)

class Pedido(models.Model):  
    consumidor = models.ForeignKey('Consumidor', on_delete=models.CASCADE, related_name='pedidos')
    dia = models.DateField(default=now)
    dia_evento = models.DateField(default=now)
    dia_pedido = models.DateField(default=now)
    dia_entrega = models.DateField(default=now)
    lugar_evento = models.CharField(max_length=50, default="")
    nos_conocio = models.IntegerField(choices=NOS_CONOCIO, default='1') # , max_length=2
    nos_conocio_coment = models.TextField(verbose_name="Comentários sobre como nos conoció", null=True, blank=True)
    email_enviado = models.BooleanField(default=False)
    variaciones = models.TextField(null=True, blank=True)

    contorno_pecho_total = models.CharField(max_length=25, null=True, blank=True)
    contorno_cintura = models.CharField(max_length=25, null=True, blank=True)
    contorno_cadera = models.CharField(max_length=25, null=True, blank=True)
    largo_talle_delante = models.CharField(max_length=25, null=True, blank=True)
    largo_talle_espalda = models.CharField(max_length=25, null=True, blank=True)
    largo_falda = models.CharField(max_length=25, null=True, blank=True)
    largo_chaqueta_delante = models.CharField(max_length=25, null=True, blank=True)
    largo_blusa_delante = models.CharField(max_length=25, null=True, blank=True)
    largo_manga_chaqueta = models.CharField(max_length=25, null=True, blank=True)
    largo_manga_blusa = models.CharField(max_length=25, null=True, blank=True)
    contorno_brazo = models.CharField(max_length=25, null=True, blank=True)
    de_hombro_a_hombro = models.CharField(max_length=25, null=True, blank=True)
    
    activo = models.BooleanField(default=True, null=False, blank=False)

    created = models.DateTimeField(auto_now_add=True) # només al crear
    updated = models.DateTimeField(auto_now=True) # cada modificació

    def __str__(self):
        return "({}) - {}".format(self.pk, self.consumidor.nombre)

    # IMPORTES

    def total_pagado(self):
        total = decimal.Decimal(0.0)
        for pago in self.pagos.all():
            total += pago.importe
        for pago in self.pagos_no_caja.all():
            total += pago.importe
        return total

    def total_pagado_(self):
        ''' Per poder crear una columna personalitzada al llistat '''
        color = 'green'
        if self.total_pagado() != self.importe_total():
            color = 'red'
        return format_html(
            '<span style="color:{};text-align:right;width:100%;display:inline-block;">{}</span>', color, self.total_pagado())

    def pendiente(self):
        return self.importe_total() - self.total_pagado()

    def articulos_str(self):
        l = [a.desc for a in self.articulos.all()]
        return ", ".join(l)

    def importe_total(self):
        l = [a.importe for a in self.articulos.all()]
        if l == []:
            return 0
        else:
            return reduce((lambda x, y: x + y), l) # suma els elements del array

    def importe_total_(self): 
        ''' Per poder crear una columna personalitzada al llistat '''
        return format_html(
            '<span style="text-align:right;width:100%;display:inline-block;">{}</span>', self.importe_total())

    class Meta:
        ordering = ['-updated']


############
# Articulo #
############

class Articulo(models.Model):
    """
        Articles relacionats amb un pedido, com pot ser, 3242 VE S.160 C.22 T.44.
        Aquests articles son línies d'entrada lliure on l'usuari pot apuntar el 
        que vol. No son articles propiament dit si no línies del pedido.
    """
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE, related_name='articulos')
    desc = models.CharField(verbose_name="Descripción", max_length=100)
    importe = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    serie = models.CharField(max_length=15, default="", null=True, blank=True)
    color = models.CharField(max_length=15, default="", null=True, blank=True)
    talla = models.CharField(choices=TALLAS, default='--', max_length=2)

    created = models.DateTimeField(auto_now_add=True) # només al crear
    updated = models.DateTimeField(auto_now=True) # cada modificació

    def __str__(self):
        return "({}) - {}".format(self.pedido.pk, self.desc)   


########
# Pago #
########

'''
    Hi ha 2 tipus de pagaments, en efectiu (Pago) i per altres mitjans (PagoNoCaja)

    VALIDATORS:
    https://stackoverflow.com/questions/54858123/how-do-i-enforce-a-positive-number-on-my-python-django-model-field
    https://docs.djangoproject.com/en/2.1/ref/models/instances/#validating-objects
    https://docs.djangoproject.com/en/2.2/ref/validators/
'''

TIPO_PAGO = (
    (1, 'TARGETA'),
    (2, 'TRANSFERENCIA'),
)

# VALIDATORS

class GreaterOrEqualToZeroValidator(BaseValidator):
    message = 'Ensure this value is greater than or equal to %(limit_value)s.'
    code = 'min_value'

    def compare(self, a, b):
        return a < b or a == b 

class GreaterThanValidator(BaseValidator):
    message = 'Ensure this value is greater than %(limit_value)s.'
    code = 'min_value'

    def compare(self, a, b):
        return a < b 

def greater_or_equal_to_zero(value):
    ''' Si el valor introduït és més petit de zero mostrem un error '''
    if value < 0:
        raise ValidationError(
            '%(value)s is not greater or equal to zero.',
            params={'value': value},
        )

def cash_payment_week_validator(value):
    ''' Quan es fa un pagament (efectiu), busquem la caixa que correspon al dia del pagament. 
        Si la caixa està oberta cap problema es pot tirar endavant l'operació.
        Si no n'hi caixa i el dia està dins de la setmana actual, creem una caixa, si no
        mostrem un error. Si ja hi ha una caixa però està tencada mostrem un error. '''
    week = get_week_by_date(value)
    res = Caja.objects.filter(year=value.year, semana=week) # , cerrada=False
    # Si no hi ha caixa
    if len(res) == 0:
        # Si el dia està dins la setmana actual podem crear la caixa
        week_actual = get_week_by_date(now())
        if week == week_actual:
            Caja.objects.create()
        else:
            raise ValidationError('Creación de caja automática solo disponible para la semana actual.')
    elif res[0].cerrada == True:
        # La fecha no està en una caixa oberta
        raise ValidationError(
            '%(value)s, esta fecha no corresponde con una caja abierta.',
            params={'value': value},
        )


# PAGO

class Pago(models.Model):
    """
        Model que guarda els pagaments només en efectiu relacionats amb un pedido i
        amb la caixa corresponent al número de setmana del dia que es fa el pagament.
        Model restrictiu ja que cal comprovar que la caixa sigui correcte.
    """
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE, related_name='pagos')
    dia = models.DateField(default=now, validators=[cash_payment_week_validator]) # 
    desc = models.CharField(verbose_name="Descripción", max_length=100)
    importe = models.DecimalField(max_digits=9, decimal_places=2, default=0, validators=[greater_or_equal_to_zero])
    # forma_pago = models.IntegerField(verbose_name="Forma de pago", choices=TIPO_PAGO, default=2)
    caja = models.ForeignKey('Caja', on_delete=models.CASCADE, related_name='pagos', null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True) # només al crear
    updated = models.DateTimeField(auto_now=True) # cada modificació 

    def __str__(self):
        return "({}) - {}".format(self.pedido.pk, self.desc)   

    def importe_(self): 
        color = 'green'
        if self.importe < 0:
            color = 'red'
        return format_html(
            '<span style="color:{};text-align:right;width:100%;display:inline-block;">{}</span>', color, self.importe)

    # def save(self, *args, **kwargs):
    #    super().save(*args, **kwargs)

# SIGNAL: PAGOS en EFECTIU

@receiver(post_save, sender=Pago)
def ensure_caja_exists(sender, instance, **kwargs):
    """ 
        Al crear o modificar un pago en efectiu ha de tenir una caixa assignada 
        segons el dia del pago. En cas de que no hi hagi cap caixa overta el
        validador cash_payment_week_validator ja la crea al validar el dia del
        pagament.
    """
    print("EL VALOR DE caja:", instance.caja)
    year = instance.dia.year
    week = get_week_by_date(instance.dia)
    # si és un pagament en efetiu ha de tenir una caixa assignada. 
    if instance.caja is None or week != instance.caja.semana:
        result = Caja.objects.get(year=year, semana=week) # get_or_create, hi ha un validator
        #if not result.cerrada: # No cal si no n'hi ha cap d'oberta el validador la crea
        instance.caja = result 
        instance.save()


################
# PAGO NO CAJA #
################

class PagoNoCaja(models.Model):
    """
        Model que guarda els pagaments fets pel client relacionats amb un pedido
        realitzat per ell pagat amb un mètode diferent del efectiu com pot ser
        targeta de crèdit, transferència, etc. Aquests pagaments només estàn
        relacionats amb el model de pedido i no tenen gaire restricció ni problemàtica.
    """
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE, related_name='pagos_no_caja')
    dia = models.DateField(default=now) 
    desc = models.CharField(verbose_name="Descripción", max_length=100)
    importe = models.DecimalField(max_digits=9, decimal_places=2, default=0, validators=[greater_or_equal_to_zero])
    forma_pago = models.IntegerField(verbose_name="Forma de pago", choices=TIPO_PAGO, default=1)
    # caja = models.ForeignKey('Caja', on_delete=models.CASCADE, related_name='pagos', null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True) # només al crear
    updated = models.DateTimeField(auto_now=True) # cada modificació 

    def __str__(self):
        return "({}) - {}".format(self.pedido.pk, self.desc)   

    def importe_(self): 
        color = 'green'
        if self.importe < 0:
            color = 'red'
        return format_html(
            '<span style="color:{};text-align:right;width:100%;display:inline-block;">{}</span>', color, self.importe)

    class Meta:
        verbose_name = "Pago No a Caja"
        verbose_name_plural = "Pagos No a Caja"


