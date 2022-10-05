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

# A r t i c u l o

class ArticuloInLineList(generics.ListCreateAPIView):
    def get_queryset(self):
        queryset = models.Articulo.objects.filter(pedido=self.kwargs["pk"])
        return queryset
    serializer_class = serializers.ArticuloSerializer

class ArticuloInLineCrud(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Articulo.objects.all()
    serializer_class = serializers.ArticuloSerializer

# P a g o

class PagoInLineList(generics.ListCreateAPIView):
    def get_queryset(self):
        queryset = models.Pago.objects.filter(pedido=self.kwargs["pk"])
        return queryset
    serializer_class = serializers.PagoSerializer

class PagooInLineCrud(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Pago.objects.all()
    serializer_class = serializers.PagoSerializer
