from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Calificacion
from auditoria.models import Log
from django.utils import timezone

@receiver(post_save, sender=Calificacion)
def log_calificacion_post_save(sender, instance, created, **kwargs):
    """
    Escucha el evento 'post_save' del modelo Calificacion.
    Crea un registro en el Log para INSERT y UPDATE.
    
    Nota: La lógica de 'DELETE' (borrado lógico) se maneja
    manualmente en 'calificacion_delete_view' porque es una
    acción especial que esta señal no puede diferenciar fácilmente.
    """

    # Si 'raw' es True, significa que los datos se están cargando
    # desde una 'fixture' (ej. loaddata), y no queremos loguear eso.
    if kwargs.get('raw', False):
        return

    # Obtenemos el usuario que está "guardado" en la calificación
    # (sea el creador o el que tomó posesión)
    usuario = instance.id_usuario
    if not usuario:
        # Si no hay usuario (ej. un registro de "Bolsa" puro
        # que fue actualizado por el sistema), no podemos loguear.
        # En nuestro caso, un Admin que edita un archivo de Bolsa
        # no toma posesión, por lo que el log no se genera (lo cual es aceptable).
        return

    if created:
        # --- Lógica de CREACIÓN (INSERT) ---
        accion = 'INSERT'
        detalle = f'Creación de Calificacion ID {instance.id_calificacion} por {usuario.nombre}'
    
    elif instance.activo:
        # --- Lógica de MODIFICACIÓN (UPDATE) ---
        # Solo logueamos si la calificación sigue activa.
        # Si 'instance.activo' es False, significa que la 'delete_view'
        # se está encargando, la cual tiene su propio log.
        accion = 'UPDATE'
        detalle = f'Modificación de Calificacion ID {instance.id_calificacion} por {usuario.nombre}'
    
    else:
        # Es un 'save' de una calificación inactiva (o un 'delete'),
        # no hacemos nada aquí.
        return

    # Crear el registro del Log
    Log.objects.create(
        fecha=timezone.now(),
        accion=accion,
        detalle=detalle,
        id_usuario=usuario,
        id_calificacion=instance
    )