from rest_framework import serializers
from .models import Calificacion, Calificaciontributaria, Factortributario
from instrumentos.models import Instrumento, Mercado
from usuarios.models import Usuario, Estado

from .forms import FACTORES_BASE_UI, FACTORES_CALCULADOS_UI, FACTORES_DIRECTOS_UI
from decimal import Decimal

class FactortributarioSerializer(serializers.ModelSerializer):
    """
    Serializa el modelo más profundo: los factores individuales.
    """
    class Meta:
        model = Factortributario
        # Solo mostramos el código y el valor
        fields = ['codigo_factor', 'valor_factor']


class CalificaciontributariaSerializer(serializers.ModelSerializer):
    """
    Serializa los datos tributarios y anida los factores.
    """
    # Usamos el serializer anterior para anidar los factores
    factortributario_set = FactortributarioSerializer(many=True, read_only=True)
    
    class Meta:
        model = Calificaciontributaria
        fields = [
            'secuencia_evento', 
            'evento_capital', 
            'anio', 
            'valor_historico', 
            'descripcion', 
            'ingreso_por_montos',
            'factortributario_set' # La lista anidada de factores
        ]


class CalificacionSerializer(serializers.ModelSerializer):
    """
    Serializa la Calificación principal (el padre de todo).
    """
    # Para los ForeignKeys, usamos StringRelatedField para mostrar
    # sus nombres (basado en el método __str__ que definimos)
    id_usuario = serializers.StringRelatedField(read_only=True)
    id_instrumento = serializers.StringRelatedField(read_only=True)
    id_mercado = serializers.StringRelatedField(read_only=True)
    id_estado = serializers.StringRelatedField(read_only=True)
    id_archivo = serializers.StringRelatedField(read_only=True)
    
    # Anidamos los datos tributarios (que a su vez anidan los factores)
    calificaciontributaria_set = CalificaciontributariaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Calificacion
        fields = [
            'id_calificacion',
            'fecha_pago',
            'fecha_registro',
            'activo',
            'id_usuario',
            'id_instrumento',
            'id_mercado',
            'id_estado',
            'id_archivo',
            'calificaciontributaria_set' # La lista anidada de datos tributarios
        ]


class CalificacionCreateSerializer(serializers.Serializer):
    """
    Este serializer valida los datos de ENTRADA para crear una calificación.
    Imita la estructura de nuestro 'CalificacionForm' (plano).
    """
    # --- Campos de Identificación ---
    # (No usamos ModelChoiceField, la vista buscará los IDs)
    mercado_nombre = serializers.CharField(max_length=100)
    instrumento_nombre = serializers.CharField(max_length=100)
    fecha_pago = serializers.DateField()
    secuencia_evento = serializers.CharField(max_length=50)
    evento_capital = serializers.CharField(max_length=100, required=False, allow_blank=True)
    anio = serializers.IntegerField()
    valor_historico = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, default=0.0)
    descripcion = serializers.CharField(required=False, allow_blank=True)
    ingreso_por_montos = serializers.BooleanField(default=False)
    
    # --- Campos de Factores/Montos (Dinámicos) ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Añadir todos los campos de factores (F08-F37) dinámicamente
        todos_los_factores = FACTORES_BASE_UI + FACTORES_CALCULADOS_UI + FACTORES_DIRECTOS_UI
        for nombre_campo in todos_los_factores:
            self.fields[nombre_campo] = serializers.DecimalField(
                max_digits=18, 
                decimal_places=8, 
                required=False, 
                default=Decimal('0.00')
            )
            
    def validate(self, data):
        """
        Validación de negocio (idéntica a la del formulario web).
        """
        if not data['ingreso_por_montos']:
            suma_factores_base = Decimal('0.0')
            for nombre_campo in FACTORES_BASE_UI:
                suma_factores_base += data.get(nombre_campo, Decimal('0.0'))
            
            if suma_factores_base > Decimal('1.00000001'):
                raise serializers.ValidationError(
                    f'Error: La suma de los factores del 8 al 19 ({suma_factores_base}) no puede ser mayor a 1.'
                )
        return data