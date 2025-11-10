from django.contrib import admin
from .models import Instrumento, Mercado
# Register your models here.

@admin.register(Instrumento)
class InstrumentoAdmin(admin.ModelAdmin):
    list_display = ('id_instrumento', 'nombre', 'tipo', 'moneda')
    search_fields = ('nombre', 'tipo', 'moneda')
    list_filter = ('tipo', 'moneda')

@admin.register(Mercado)
class MercadoAdmin(admin.ModelAdmin):
    list_display = ('id_mercado', 'nombre', 'pais', 'tipo')
    search_fields = ('nombre', 'pais', 'tipo')
    list_filter = ('pais', 'tipo')

    
