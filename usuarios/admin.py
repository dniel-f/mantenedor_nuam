from django.contrib import admin
from .models import Rol, Usuario, Estado
import bcrypt 
# Register your models here.

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id_rol', 'nombre', 'descripcion')
    search_fields = ('nombre',)
    list_filter = ()

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'nombre','correo', 'id_rol', 'fecha_creacion', 'id_estado')
    search_fields = ('nombre', 'correo')
    list_filter = ('id_rol', 'id_estado')
    
    # Especificamos qué campos mostrar en el formulario de creación/edición
    # Ocultamos el 'contrasena_hash' por defecto
    fields = ('nombre', 'correo', 'id_rol', 'id_estado', 'contrasena_hash')
    # Hacemos que el hash solo se muestre en modo "lectura" para no confundir
    readonly_fields = ('fecha_creacion',)

    def save_model(self, request, obj, form, change):
        """
        Sobreescribimos el guardado para hashear la contraseña 
        si se ingresó como texto plano.
        """
        # 'obj.contrasena_hash' tiene el valor del campo del formulario
        if obj.contrasena_hash:
            password_texto = obj.contrasena_hash 

            # Verificamos si NO es un hash (no empieza con '$2b$')
            # Es decir, si es texto plano (como 'Nuam01' o 'hash_placeholder')
            if not password_texto.startswith('$2b$'):
                # Es texto plano, ¡necesitamos hashearlo!
                password_bytes = password_texto.encode('utf-8')
                salt = bcrypt.gensalt()
                hash_bytes = bcrypt.hashpw(password_bytes, salt)
                
                # Reemplazamos el texto plano por el hash real
                obj.contrasena_hash = hash_bytes.decode('utf-8')

        # Guardamos el objeto (ahora con el hash correcto)
        super().save_model(request, obj, form, change)


@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ('id_estado', 'nombre', 'descripcion')
    search_fields = ('nombre',)
    list_filter = ()