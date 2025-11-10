from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import Rol

def login_requerido_personalizado(view_func):
    """
    Verifica que el usuario esté logueado en nuestra sesión personalizada.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'id_usuario' not in request.session:
            messages.error(request, 'Debes iniciar sesión para ver esta página.')
            return redirect('usuarios:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def rol_requerido(roles_permitidos=[]):
    """
    Decorador que verifica si el rol del usuario está en la lista permitida.
    'roles_permitidos' es una lista de strings, ej: ['Corredor', 'Administrador']
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Primero, aseguramos que esté logueado
            if 'id_usuario' not in request.session:
                messages.error(request, 'Debes iniciar sesión para ver esta página.')
                return redirect('usuarios:login')
            
            # Obtenemos el nombre del rol desde la sesión
            rol_nombre = request.session.get('rol_nombre', 'Desconocido')
            
            # Verificamos si tiene permiso
            if rol_nombre not in roles_permitidos:
                messages.error(request, 'No tienes permisos para acceder a esta sección.')
                # Lo enviamos al home, no al login (porque ya está logueado)
                return redirect('home') 
            
            # Si tiene el rol, dejamos que continúe
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator