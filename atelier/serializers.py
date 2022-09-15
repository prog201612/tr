# https://www.django-rest-framework.org/api-guide/serializers/#modelserializer
from rest_framework import serializers
from . import models

# P r o t o t y p e   N a m e

class ConsumidorSerializer(serializers.ModelSerializer):
    class Meta:
        model= models.Consumidor
        fields =  '__all__' # ('nombre', 'telefono', 'direccion', 'email')
        #read_only_fields = ("created", "updated", "id",)

    def create(self, validated_data):
        consumidor = models.Consumidor(
            email=validated_data['email'],
            nombre=validated_data['nombre'],
            telefono=validated_data['telefono'],
            direccion=validated_data['direccion']
        )
        consumidor.save()
        return consumidor


class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model= models.Pedido
        fields = '__all__'
        #read_only_fields = ("nombre_consumidor",)

    # Readonly fields
    nombre_consumidor = serializers.ReadOnlyField()