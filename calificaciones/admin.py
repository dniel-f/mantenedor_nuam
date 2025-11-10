from django.contrib import admin
from .models import Calificacion, Calificaciontributaria, Factortributario

# --- IMPORTACIONES ADICIONALES ---
from auditoria.models import Log  # Importamos el modelo Log
from usuarios.models import Usuario # Importamos tu modelo Usuario
from django.utils import timezone # Para registrar la fecha del log

# --- FUNCIÓN AUXILIAR ---
def get_usuario_app(request_user):
    """
    Busca el 'Usuario' de nuestra app usando el email 
    del 'User' (admin) de Django.
    """
    try:
        # request_user es el usuario de admin de Django
        # Buscamos en nuestra tabla 'Usuario' por el email
        usuario_app = Usuario.objects.get(correo=request_user.email)
        return usuario_app
    except Usuario.DoesNotExist:
        # Si no se encuentra, no podemos loguear.
        # En producción, aquí podrías loguear este error.
        print(f"Error de Auditoría: No se encontró un 'Usuario' con el email {request_user.email}")
        return None

# --- ACCIÓN DE BORRADO LÓGICO ---
@admin.action(description='Dar de baja calificaciones seleccionadas (Borrado Lógico)')
def desactivar_calificaciones(modeladmin, request, queryset):
    """
    Acción de admin para 'eliminar' (desactivar) calificaciones.
    """
    # 1. Obtenemos el usuario de nuestra app
    usuario_app = get_usuario_app(request.user)
    
    # 2. Actualizamos el campo 'activo' a False
    count = queryset.update(activo=False)
    
    # 3. Registramos en el Log (si encontramos al usuario)
    if usuario_app:
        fecha_actual = timezone.now()
        for obj in queryset:
            Log.objects.create(
                fecha=fecha_actual,
                accion='DELETE', # Usamos DELETE para "borrado lógico"
                detalle=f'Borrado lógico de Calificacion ID {obj.id_calificacion} por admin.',
                id_usuario=usuario_app,
                id_calificacion=obj
            )
    
    modeladmin.message_user(request, f'{count} calificaciones han sido dadas de baja (borrado lógico).')


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    
    # Sobreescribimos get_queryset para que el Admin vea TODO (activos e inactivos)
    def get_queryset(self, request):
        return Calificacion.objects_all.all()

    list_display = (
        'id_calificacion', 'monto', 'factor', 'fecha_emision', 
        'fecha_pago', 'id_usuario', 'id_instrumento', 
        'id_mercado', 'id_estado', 
        'activo', # <- AÑADIDO
        'fecha_registro'
    )
    search_fields = ('id_usuario__nombre', 'id_instrumento__nombre')
    list_filter = ('fecha_emision', 'fecha_pago', 'id_estado', 'activo') # <- AÑADIDO
    
    # Añadimos nuestra acción personalizada
    actions = [desactivar_calificaciones]

    # --- MÉTODO PARA AUDITORÍA DE GUARDADO ---
    def save_model(self, request, obj, form, change):
        """
        Sobreescribimos el guardado para registrar en el Log.
        'change' es True si es una modificación, False si es uno nuevo.
        """
        # 1. Guardar el objeto primero
        super().save_model(request, obj, form, change)

        # 2. Obtenemos el usuario de nuestra app
        usuario_app = get_usuario_app(request.user)

        # Si no encontramos usuario, no podemos loguear
        if not usuario_app:
            return

        # 3. Determinar la acción y el detalle
        accion_log = 'UPDATE' if change else 'INSERT'
        detalle_log = f'Modificación de Calificacion ID {obj.id_calificacion} por admin.'
        if not change:
            # Si es nuevo, actualizamos fecha_registro (ya que auto_now_add no funciona con managed=False)
            if not obj.fecha_registro:
                 obj.fecha_registro = timezone.now()
                 obj.save() # Guardamos de nuevo solo para la fecha
            
            detalle_log = f'Creación de Calificacion ID {obj.id_calificacion} por admin.'
            
        # 4. Crear el registro en Log
        Log.objects.create(
            fecha=timezone.now(),
            accion=accion_log,
            detalle=detalle_log,
            id_usuario=usuario_app, 
            id_calificacion=obj
        )
        

@admin.register(Calificaciontributaria)
class CalificaciontributariaAdmin(admin.ModelAdmin):
    list_display = ('id_calificacion_tributaria', 'id_calificacion', 'secuencia_evento', 'evento_capital', 'anio', 'valor_historico', 'descripcion', 'ingreso_por_montos')
    search_fields = ('secuencia_evento', 'evento_capital')
    list_filter = ('anio',)

@admin.register(Factortributario)
class FactortributarioAdmin(admin.ModelAdmin):
    list_display = ('id_factor', 'id_calificacion_tributaria', 'codigo_factor', 'descripcion_factor', 'valor_factor')
    search_fields = ('codigo_factor', 'descripcion_factor')
    list_filter = ()