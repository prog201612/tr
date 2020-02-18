from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save

from .models import Pago, PagoNoCaja, NOTIFICATION_TYPE_NEW_PAYMENT, NOTIFICATION_TYPE_EDIT_PAYMENT, \
                    NOTIFICATION_TYPE_DEL_PAYMENT, Notification, get_week_by_date, Caja


HOST = "127.0.0.1:8000"

def pago_create_notification(instance, created, pago_url):
    if created:
        NOTIFICATION_TYPE = NOTIFICATION_TYPE_NEW_PAYMENT
        desc = f'<a href="http://{HOST}/atelier/{pago_url}/{instance.pk}/change/">Añadido {pago_url} Nº: {instance.pk}</a>'
    else:
        NOTIFICATION_TYPE = NOTIFICATION_TYPE_EDIT_PAYMENT
        desc = f'<a href="http://{HOST}/atelier/{pago_url}/{instance.pk}/change/">Modificado {pago_url} Nº: {instance.pk}</a>'
    Notification.new_notification( NOTIFICATION_TYPE, desc )
    print("[PCR] - Added Notification")


@receiver(post_save, sender=Pago)
def pago_post_save_signal(sender, instance, created, **kwargs):
    pago_create_notification(instance, created, 'pago')


@receiver(post_save, sender=PagoNoCaja)
def pagonocaja_post_save_signal(sender, instance, created, **kwargs):
    pago_create_notification(instance, created, 'pagonocaja')


@receiver(post_delete, sender=Pago)
def pago_post_delete_signal(sender, instance, **kwargs):
    desc = f'Eliminado pago Nº: {instance.pk}, Pedido: {instance.pedido}, Dia: {instance.dia}, Importe: {instance.importe}, Caja: {instance.caja}'
    Notification.new_notification( NOTIFICATION_TYPE_DEL_PAYMENT, desc )


@receiver(post_delete, sender=PagoNoCaja)
def pagonocaja_post_delete_signal(sender, instance, **kwargs):
    desc = f'Eliminado pagoNoCaja Nº: {instance.pk}, Pedido: {instance.pedido}, Dia: {instance.dia}, Desc: {instance.desc}, FormaPago: {instance.forma_pago}'
    Notification.new_notification( NOTIFICATION_TYPE_DEL_PAYMENT, desc )


# SIGNAL: PAGOS en EFECTIU

@receiver(pre_save, sender=Pago)
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
        # instance.save()


# SIGNALS Caja: Creació de caixes intermitges automatitzada

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
        # Si l'any de la última caja existent <= a l'any de la caja actual i any1seman1 (200054) < an2semana2 (200057)
        if int(any1) <= int(any2) and int("{}{:02d}".format(any1, semana1)) < int("{}{:02d}".format(any2, semana2)) - 1:
            semana2 -= 1
            # Si arrivem a la setmana zero, començem desde l'última setmana de l'any anterior
            if semana2 == 0:
                semana2 = 52
                any2 -=1
            # Creem la caixa anterior a la actual.
            new = Caja(year=any2, semana=semana2, caja_siguiente=instance)
            new.save()