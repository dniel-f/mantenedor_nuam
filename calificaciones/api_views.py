from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP

# Modelos
from .models import Calificacion, Calificaciontributaria, Factortributario
from instrumentos.models import Instrumento, Mercado
from usuarios.models import Estado

# Serializers
from .serializers import CalificacionSerializer, CalificacionCreateSerializer

# Listas de Factores (para la lógica de cálculo)
from .forms import FACTORES_BASE_UI, FACTORES_CALCULADOS_UI, FACTORES_DIRECTOS_UI

# ==========================================================
#  API VIEWSET (LECTURA Y ESCRITURA)
# ==========================================================
class CalificacionViewSet(
    mixins.CreateModelMixin,  # Permite POST (Crear)
    mixins.RetrieveModelMixin, # Permite GET /<id>/ (Detalle)
    mixins.ListModelMixin,     # Permite GET / (Listar)
    viewsets.GenericViewSet
):
    """
    API endpoint para Calificaciones (CU13-15).
    - GET (Listar): Muestra calificaciones (con lógica de privacidad).
    - GET (Detalle): Muestra una calificación.
    - POST (Crear): Permite a un sistema externo crear una calificación.
    """
    permission_classes = [IsAuthenticated] # Requiere token JWT

    def get_serializer_class(self):
        """
        Usa un serializer diferente para 'Crear' (POST) 
        que para 'Leer' (GET).
        """
        if self.action == 'create':
            return CalificacionCreateSerializer # El serializer plano (input)
        return CalificacionSerializer # El serializer anidado (output)

    def get_queryset(self):
        """
        --- LÓGICA DE 'LOCALIDAD' (PRIVACIDAD) USANDO JWT ---
        Filtra los resultados basado en el rol del usuario del token.
        """
        # 'self.request.user' ES nuestro objeto 'Usuario' 
        usuario = self.request.user 
        
        qs_base = Calificacion.objects.select_related(
            'id_instrumento', 'id_mercado', 'id_usuario', 'id_estado'
        ).prefetch_related(
            'calificaciontributaria_set__factortributario_set'
        )
        
        # Los roles 'Administrador' o 'Auditor' ven todo
        if usuario.id_rol.nombre in ['Administrador', 'Auditor']:
            qs = qs_base.all()
        else:
            # Un 'Corredor' solo ve sus cargas manuales o las de 'Archivo'
            qs = qs_base.filter(
                Q(id_usuario=usuario) | 
                Q(id_usuario__isnull=True)
            )
        

        
        return qs.order_by('-fecha_registro')

    @transaction.atomic
    def perform_create(self, serializer):
        """
        Sobreescribimos el método 'POST' para guardar en las 3 tablas.
        Esta lógica es idéntica a 'calificacion_create_view'.
        """
        data = serializer.validated_data
        
        # El 'usuario_app' es quien hace la petición
        usuario_app = self.request.user 
        
        # --- LÓGICA DE GUARDADO (Copiada de 'calificacion_create_view') ---
        try:
            estado_activo = get_object_or_404(Estado, nombre='Activo')
            instrumento, _ = Instrumento.objects.get_or_create(
                nombre=data['instrumento_nombre'],
                defaults={'tipo': 'Desconocido', 'moneda': 'N/A'}
            )
            mercado, _ = Mercado.objects.get_or_create(
                nombre=data['mercado_nombre'],
                defaults={'pais': 'N/A'}
            )

            # 1. Crear 'Calificacion' (Padre)
            # Un sistema externo (API) crea un registro 'Archivo'
            nueva_calificacion = Calificacion.objects.create(
                fecha_pago=data['fecha_pago'],
                id_usuario=None, # ¡La API crea registros de "Bolsa"!
                id_instrumento=instrumento,
                id_mercado=mercado,
                id_archivo=None, # Opcional: podríamos crear un 'Archivo' aquí
                id_estado=estado_activo,
                fecha_registro=timezone.now(),
                activo=True 
            )

            # 2. Crear 'CalificacionTributaria' (Hijo)
            nueva_calif_trib = Calificaciontributaria.objects.create(
                id_calificacion=nueva_calificacion,
                secuencia_evento=data['secuencia_evento'],
                evento_capital=data.get('evento_capital', ''),
                anio=data['anio'],
                valor_historico=data['valor_historico'],
                descripcion=data.get('descripcion', 'Carga vía API'),
                ingreso_por_montos=data['ingreso_por_montos']
            )

            # 3. Lógica de Cálculo (Montos vs. Factores)
            valores_finales = {} # { 'F08': Decimal(0.5), ... }
            
            if data['ingreso_por_montos']:
                suma_total_montos = Decimal('0.0')
                for campo in FACTORES_BASE_UI: # 'factor_08', 'factor_09'...
                    suma_total_montos += data.get(campo, Decimal('0.0'))
                
                precision = Decimal('0.00000001')
                if suma_total_montos > 0:
                    for campo in FACTORES_BASE_UI + FACTORES_CALCULADOS_UI:
                        monto = data.get(campo, Decimal('0.0'))
                        factor_calc = (monto / suma_total_montos).quantize(precision, rounding=ROUND_HALF_UP)
                        codigo_db = f"F{campo.split('_')[-1].zfill(2)}"
                        valores_finales[codigo_db] = factor_calc
                else:
                    for campo in FACTORES_BASE_UI + FACTORES_CALCULADOS_UI:
                        codigo_db = f"F{campo.split('_')[-1].zfill(2)}"
                        valores_finales[codigo_db] = Decimal('0.0')
                
                for campo in FACTORES_DIRECTOS_UI:
                    codigo_db = f"F{campo.split('_')[-1].zfill(2)}"
                    valores_finales[codigo_db] = data.get(campo, Decimal('0.0'))
            
            else:
                # Ingreso directo de Factores
                todos_los_factores = FACTORES_BASE_UI + FACTORES_CALCULADOS_UI + FACTORES_DIRECTOS_UI
                for campo in todos_los_factores:
                    codigo_db = f"F{campo.split('_')[-1].zfill(2)}"
                    valores_finales[codigo_db] = data.get(campo, Decimal('0.0'))
            
            # 4. Crear 'Factortributario' (Nietos)
            factores_para_crear = []
            for codigo_db, valor_factor in valores_finales.items():
                if valor_factor != Decimal('0.0'):
                    factores_para_crear.append(
                        Factortributario(
                            id_calificacion_tributaria=nueva_calif_trib,
                            codigo_factor=codigo_db,
                            descripcion_factor=f"Factor-{codigo_db[1:]}",
                            valor_factor=valor_factor
                        )
                    )
            if factores_para_crear:
                Factortributario.objects.bulk_create(factores_para_crear)
            
        except Exception as e:
            raise serializers.ValidationError(f"Error al guardar: {e}")