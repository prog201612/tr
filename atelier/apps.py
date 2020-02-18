from django.apps import AppConfig


class AtelierConfig(AppConfig):
    name = 'atelier'
    
    def ready(self):
        from . import signals 
