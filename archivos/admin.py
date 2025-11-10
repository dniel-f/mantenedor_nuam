from django.contrib import admin

# Register your models here.

from .models import Archivo

@admin.register(Archivo)
class ArchivoAdmin(admin.ModelAdmin):
    list_display = ('id_archivo', 'nombre_archivo', 'fecha_carga', 'estado_validacion', 'ruta', 'id_usuario', 'id_estado')
    search_fields = ('nombre_archivo', 'estado_validacion')
    list_filter = ('estado_validacion', 'fecha_carga')