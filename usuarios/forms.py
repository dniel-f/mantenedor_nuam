from django import forms
from .models import Usuario
from .models import Rol, Estado
import bcrypt
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.utils.translation import gettext_lazy as _



class LoginForm(forms.Form):
    correo = forms.EmailField(
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'usuario@mail.com'})
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )

    def clean(self):
        cleaned_data = super().clean()
        correo = cleaned_data.get('correo')
        password = cleaned_data.get('password') # Contraseña en string (de la web)

        if correo and password:
            try:
                # 1. Buscamos al usuario por su correo
                usuario = Usuario.objects.get(correo=correo)
                
                # 2. Verificamos su estado (Asumiendo 5 = 'Activo' de tu BBDD)
                if usuario.id_estado_id != 5:
                    raise forms.ValidationError('Esta cuenta de usuario está inactiva.')

                # 3. Verificamos la contraseña (¡Modo Seguro con BCRYPT!)
                
                # Convertimos el password ingresado (string) a bytes
                password_bytes = password.encode('utf-8')
                
                # Convertimos el hash guardado (string) a bytes
                hash_bytes = usuario.contrasena_hash.encode('utf-8')
                
                # Comparamos con bcrypt
                if not bcrypt.checkpw(password_bytes, hash_bytes):
                    raise forms.ValidationError('Correo o contraseña incorrectos.')
                
                # Guardamos el usuario encontrado en el formulario
                cleaned_data['usuario'] = usuario

            except Usuario.DoesNotExist:
                raise forms.ValidationError('Correo o contraseña incorrectos.')
        
        return cleaned_data
    
# ==========================================================
#  Formulario de Filtros para la Grilla de Usuarios
# ==========================================================
class UserFilterForm(forms.Form):
    
    # Usamos CharField (no ModelChoice) para buscar por 'contiene'
    nombre = forms.CharField(
        label='Nombre',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre o correo'})
    )
    
    id_rol = forms.ModelChoiceField(
        queryset=Rol.objects.all(),
        required=False,
        label='Rol',
        empty_label='-- Todos los Roles --',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    id_estado = forms.ModelChoiceField(
        queryset=Estado.objects.all(),
        required=False,
        label='Estado',
        empty_label='-- Todos los Estados --',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


# ==========================================================
#  Formulario para Crear/Editar Usuarios (CU6)
# ==========================================================
class UserForm(forms.ModelForm):
    """
    Formulario para crear y modificar usuarios, con manejo de contraseña.
    """
    # Sobreescribimos el campo 'contrasena_hash' para hacerlo 'password'
    password = forms.CharField(
        label='Contraseña',
        required=False, # No es requerida al *modificar*
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Dejar en blanco para no cambiar la contraseña al modificar."
    )
    
    class Meta:
        model = Usuario
        # Campos que mostraremos en el formulario
        fields = ['nombre', 'correo', 'id_rol', 'id_estado', 'password']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'id_rol': forms.Select(attrs={'class': 'form-select'}),
            'id_estado': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si estamos editando (instance=True), la contraseña no es requerida
        if self.instance.pk:
            self.fields['password'].required = False
        else:
            # Si estamos creando, sí es requerida
            self.fields['password'].required = True

    def clean_correo(self):
        """
        Validar que el correo sea único.
        """
        correo = self.cleaned_data.get('correo')
        
        # Si estamos editando (self.instance.pk), 
        # excluimos al propio usuario de la validación
        query = Usuario.objects.filter(correo__iexact=correo)
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
            
        if query.exists():
            raise forms.ValidationError("Ya existe un usuario con este correo electrónico.")
        return correo

    def save(self, commit=True):
        """
        Sobreescribimos el 'save' para hashear la contraseña.
        """
        usuario = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        if password:
            # Si se proporcionó una nueva contraseña, la hasheamos
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hash_bytes = bcrypt.hashpw(password_bytes, salt)
            usuario.contrasena_hash = hash_bytes.decode('utf-8')
        
        if commit:
            usuario.save()
        return usuario
    
# ==========================================================
#  Serializer de Token JWT Personalizado (para API)
# ==========================================================
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para que JWT valide contra
    nuestra tabla 'Usuario' y use 'bcrypt'.
    """

    @classmethod
    def get_token(cls, user):
        # 'user' aquí es nuestro objeto 'Usuario' (de la app)
        token = super().get_token(user)

        # Añadimos el rol y el nombre, para que las vistas de API
        # sepan quién es el usuario y qué permisos tiene.
        token['nombre'] = user.nombre
        token['rol'] = user.id_rol.nombre
        token['id_usuario_app'] = user.id_usuario
        
        return token

    def validate(self, attrs):
        # 'attrs' contiene el 'correo' y 'password' del JSON
        correo = attrs.get('username') # 'username' es el nombre por defecto del campo
        password = attrs.get('password')

        if not correo or not password:
            raise serializers.ValidationError(_('Se requieren "correo" y "password".'))

        # --- Lógica de Validación Personalizada ---
        try:
            # 1. Buscar al usuario en nuestra tabla
            usuario = Usuario.objects.select_related('id_rol').get(correo=correo)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError(_('No se encontró un usuario con ese correo.'))

        # 2. Verificar estado
        if usuario.id_estado.nombre != 'Activo':
             raise serializers.ValidationError(_('Esta cuenta de usuario está inactiva.'))

        # 3. Verificar contraseña (con bcrypt)
        password_bytes = password.encode('utf-8')
        hash_bytes = usuario.contrasena_hash.encode('utf-8')

        if not bcrypt.checkpw(password_bytes, hash_bytes):
            raise serializers.ValidationError(_('Correo o contraseña incorrectos.'))

        # El 'user' que devolvemos aquí es el que se pasa a get_token
        self.user = usuario

        # Reemplazamos 'attrs' por el resultado del token
        # (Esto es estándar de DRF Simple JWT)
        refresh = self.get_token(self.user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return data