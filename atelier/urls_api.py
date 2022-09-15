from rest_framework.routers import DefaultRouter
from django.urls import path

from tr.apiviews import CustomAuthToken

from .apiviews import ConsumidorViewSet, PedidoViewSet
from rest_framework.authtoken import views
# https://www.django-rest-framework.org/api-guide/authentication/#generating-tokens
# settings: afegir app -> 'rest_framework.authtoken' i fer un migrate de la base de dades
# POST api/v1/api-token-auth/ amb: username/password JSON (important l'últim /)
# return: {"token":"83fbb88c3011fc3449217cb963dc6497dda9a185"}

# SOBRETOT!!!! Al fer les putes crides a una api, posar el putu / al final, per exemple:
# http://localhost:8000/api/v1/consumidor/?format=json
# HEADERS:
#  - Authorization: Token 8cb6a6ff15b2114b6fdf17570118f2148e0164ab
#  - Content-Type: application/json

# DRF
router = DefaultRouter()
# Cal posar els headers correctes i el token i acabar la url amb /?format=json
router.register('v1/consumidor', ConsumidorViewSet, basename='v1_consumidor')
router.register('v1/pedido', PedidoViewSet, basename='v1_consumidor')

api_patterns = ([
   # Per fer l'authenticació amb usrer/password i rebre el token
   # path('v1/api-token-auth/', views.obtain_auth_token), 
    path('v1/api-token-auth/', CustomAuthToken.as_view()),
] + router.urls, 'api')