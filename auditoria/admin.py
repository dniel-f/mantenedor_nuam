from django.contrib import admin
from .models import Auditoria, Log

# Register your models here.

@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ('id_auditoria', 'fecha', 'tipo', 'resultado', 'observaciones', 'id_usuario', 'id_calificacion')
    search_fields = ('tipo', 'resultado')
    list_filter = ('tipo', 'fecha')

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('id_log', 'fecha', 'accion', 'detalle', 'id_usuario', 'id_calificacion')
    search_fields = ('accion',)
    list_filter = ('accion', 'fecha')

