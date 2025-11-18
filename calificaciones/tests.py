from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

# Importamos los modelos para verificar la BBDD directamente
from .models import Calificacion, Factortributario
from usuarios.models import Usuario

# NOTA: Estas pruebas ASUMEN que la BBDD ha sido poblada
# con el script SQL ('seed.sql') o el 'seed_data.json'.
# Se deben ejecutar con: python manage.py test --keepdb


class CalificacionAPITests(APITestCase):

    # --- DATOS DE PRUEBA (Basados en el script seed.sql) ---
    # Contraseña para todos los usuarios del seed
    PASSWORD_PRUEBA = 'admin123'
    
    # Usuarios del Seed
    EMAIL_CORREDOR_A = 'corredor_a@mail.com'
    EMAIL_CORREDOR_B = 'corredor_b@mail.com'
    EMAIL_ADMIN = 'admin@mail.com'
    
    # IDs de Calificaciones del Seed
    ID_CALIF_CORREDOR_A = 1
    ID_CALIF_CORREDOR_B = 2
    ID_CALIF_ARCHIVO = 3

    def _get_jwt_token(self, email):
        """Función auxiliar para iniciar sesión en la API y obtener un token."""
        url = '/api/token/'
        data = {
            'username': email,
            'password': self.PASSWORD_PRUEBA
        }
        response = self.client.post(url, data, format='json')
        
        # Asegurarnos de que el login funciona
        self.assertEqual(response.status_code, status.HTTP_200_OK, 
                         f"No se pudo obtener el token para {email}. ¿Contraseña correcta?")
        
        return response.data['access']

    # =============================================
    # PRUEBA 1: Seguridad de Roles (GET)
    # (Criterio 3.1.3.5 / CU4)
    # =============================================
    def test_corredor_a_ve_solo_sus_datos(self):
        """
        Prueba que el 'Corredor A' solo puede ver sus datos (ID 1)
        y los de Archivo (ID 3), pero NO los del 'Corredor B' (ID 2).
        """
        print("Ejecutando Test: test_corredor_a_ve_solo_sus_datos...")
        
        # 1. Obtener token para Corredor A
        token = self._get_jwt_token(self.EMAIL_CORREDOR_A)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # 2. Hacer petición GET a la API
        response = self.client.get('/api/v1/calificaciones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Analizar resultados
        # 'response.data['results']' contiene la lista de calificaciones
        ids_recibidos = [item['id_calificacion'] for item in response.data['results']]
        
        # 4. Validar (Assert)
        self.assertIn(self.ID_CALIF_CORREDOR_A, ids_recibidos, 
                      "El Corredor A no puede ver su propia calificación (ID 1)")
        self.assertIn(self.ID_CALIF_ARCHIVO, ids_recibidos, 
                      "El Corredor A no puede ver la calificación de Archivo (ID 3)")
        self.assertNotIn(self.ID_CALIF_CORREDOR_B, ids_recibidos, 
                         "¡Error de Seguridad! El Corredor A PUEDE VER los datos del Corredor B (ID 2)")

    # =============================================
    # PRUEBA 2: Lógica de Cálculo (POST)
    # (Criterio 3.1.1.1 / CU13)
    # =============================================
    def test_api_calcula_factores_desde_montos(self):
        """
        Prueba que el endpoint POST (/api/v1/calificaciones/)
        calcula correctamente los factores si 'ingreso_por_montos' es True.
        """
        print("Ejecutando Test: test_api_calcula_factores_desde_montos...")

        # 1. Obtener token de Admin (para tener permisos de POST)
        token = self._get_jwt_token(self.EMAIL_ADMIN)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # 2. Definir el JSON (Montos) que enviaremos
        datos_post = {
            "mercado_nombre": "ACN",
            "instrumento_nombre": "Test API Cálculo",
            "fecha_pago": "2025-12-01",
            "secuencia_evento": "API-TEST-100",
            "anio": 2025,
            "ingreso_por_montos": True,
            "Monto_08": "100.00", # (Usamos strings como en un JSON real)
            "Monto_09": "300.00",
            "Monto_20": "50.00" # (Monto de crédito)
        }
        
        # 3. Hacer la petición POST
        response = self.client.post('/api/v1/calificaciones/', datos_post, format='json')
        
        # 4. Validar que se creó (201 Created)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         f"El POST falló. Error: {response.data}")
        
        # 5. Verificar los cálculos en la BBDD
        id_nueva_calif = response.data['id_calificacion']
        
        # Suma total de montos base (8-19) = 100 + 300 = 400
        
        # Factor 8 esperado = 100 / 400 = 0.25
        f08 = Factortributario.objects.get(
            id_calificacion_tributaria__id_calificacion_id=id_nueva_calif, 
            codigo_factor='F08'
        )
        self.assertEqual(f08.valor_factor, Decimal('0.25000000'))

        # Factor 9 esperado = 300 / 400 = 0.75
        f09 = Factortributario.objects.get(
            id_calificacion_tributaria__id_calificacion_id=id_nueva_calif, 
            codigo_factor='F09'
        )
        self.assertEqual(f09.valor_factor, Decimal('0.75000000'))
        
        # Factor 20 esperado (crédito) = 50 / 400 = 0.125
        f20 = Factortributario.objects.get(
            id_calificacion_tributaria__id_calificacion_id=id_nueva_calif, 
            codigo_factor='F20'
        )
        self.assertEqual(f20.valor_factor, Decimal('0.12500000'))