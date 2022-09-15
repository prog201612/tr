from rest_framework import viewsets
from rest_framework import generics

from . import models
from . import serializers

# C o n s u m i d o r

class ConsumidorViewSet(viewsets.ModelViewSet):
    queryset = models.Consumidor.objects.all()
    serializer_class = serializers.ConsumidorSerializer

# P e d i d o

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = models.Pedido.objects.all()
    serializer_class = serializers.PedidoSerializer
