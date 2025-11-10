from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings
from .models import Usuario # ¡Importamos nuestro modelo!

class CustomJWTAuthentication(JWTAuthentication):
    """
    Autenticación personalizada que busca en el modelo 'Usuario'
    en lugar del 'User' por defecto de Django.
    """
    
    def get_user(self, validated_token):
        """
        Sobreescribimos el método 'get_user' para que
        busque en la tabla 'usuario' usando 'id_usuario'.
        """
        try:
            # Obtenemos el ID del usuario del token
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            # (Manejo de error si el token está malformado)
            return None 

        try:
            # Buscamos en 'Usuario.objects' usando 'id_usuario'
            user = Usuario.objects.select_related('id_rol', 'id_estado').get(id_usuario=user_id)
        except Usuario.DoesNotExist:
            return None

        return user