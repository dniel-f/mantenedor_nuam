from django import forms
from instrumentos.models import Mercado, Instrumento
from .models import Calificacion, Calificaciontributaria, Factortributario
import datetime
from decimal import Decimal

# --- Definiciones de Años ---
YEAR_CHOICES_FILTER = [(y, y) for y in range(datetime.date.today().year, datetime.date.today().year - 10, -1)]
YEAR_CHOICES_CREATE = [(y, y) for y in range(datetime.date.today().year + 1, datetime.date.today().year - 10, -1)]

# ==========================================================
#  CLASE 1: Formulario de Filtros (HD-1)
# ==========================================================
class CalificacionFilterForm(forms.Form):
    # ... (Esta clase no cambia)
    mercado = forms.ModelChoiceField(
        queryset=Mercado.objects.all(),
        required=False,
        label='Mercado',
        empty_label='-- Todos los Mercados --',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    anio = forms.ChoiceField(
        choices=[('', '-- Todos los Años --')] + YEAR_CHOICES_FILTER,
        required=False,
        label='Año Comercial',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    ORIGEN_CHOICES = (
        ('', '-- Todos los Orígenes --'),
        ('manual', 'Carga Manual (Corredor)'),
        ('archivo', 'Carga de Archivo (Sistema)'),
    )
    origen = forms.ChoiceField(
        choices=ORIGEN_CHOICES,
        required=False,
        label='Origen',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

# --- CAMBIO: Definición de grupos de factores (ahora con Factor 19) ---
# Factores base para el cálculo del denominador (8-19)
FACTORES_BASE_UI = [
    'factor_08', 'factor_09', 'factor_10', 'factor_11', 'factor_12', 
    'factor_13', 'factor_14', 'factor_15', 'factor_16', 'factor_17', 
    'factor_18', 'factor_19' # <-- CAMBIO de 19A a 19
]
# Factores que son calculados (numerador / suma(8-19))
FACTORES_CALCULADOS_UI = [
    'factor_20', 'factor_21', 'factor_22', 'factor_23', 'factor_24',
    'factor_25', 'factor_26', 'factor_27', 'factor_28', 'factor_29',
    'factor_30', 'factor_31', 'factor_32', 'factor_33'
]
# Factores de ingreso directo (TEF, TEX, etc.)
FACTORES_DIRECTOS_UI = [
    'factor_34', 'factor_35', 'factor_36', 'factor_37'
]

# ==========================================================
#  CLASE 2: Formulario de Creación/Edición (HD-2)
# ==========================================================
class CalificacionForm(forms.Form):
    # ... (Campos de 'Calificacion' no cambian) ...
    mercado = forms.ModelChoiceField(
        queryset=Mercado.objects.all(),
        label='Mercado',
        empty_label='Seleccione un Mercado',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    instrumento_nombre = forms.CharField(
        label='Instrumento (Nombre)',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    fecha_pago = forms.DateField(
        label='Fecha Pago',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    secuencia_evento = forms.CharField(
        label='Secuencia Evento',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    evento_capital = forms.CharField(
        label='Evento Capital',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    anio = forms.ChoiceField(
        choices=[('', 'Seleccione Año')] + YEAR_CHOICES_CREATE,
        label='Año',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    valor_historico = forms.DecimalField(
        label='Valor Histórico', required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    descripcion = forms.CharField(
        label='Descripción', required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    ingreso_por_montos = forms.BooleanField(
        label='Ingreso por Montos', required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # --- CAMBIO: Nombres de factores ahora usa 19 (no 19A) ---
        nombres_factores = {
            'factor_08': 'Factor-08 No Constitutiva de Renta No Acogido a Impto',
            'factor_09': 'Factor-09 Impto. 1ra Caetg. Afecto GI. Comp. Con Devolución',
            'factor_10': 'Factor-10 Impuesto Tasa Adicional Exento Art. 21',
            'factor_11': 'Factor-11 Incremento Impuesto 1ra Categoría',
            'factor_12': 'Factor-12 Impto. 1ra Categ Exento GI. Comp. Con Devolución',
            'factor_13': 'Factor-13 Impto. 1ra Categ. Afecto GI. Comp. Sin Devoución',
            'factor_14': 'Factor-14 Impto. 1ra Categg. Exento GI. Comp. Sin Devolución',
            'factor_15': 'Factor-15 Impro. Créditos pro Impuestos Externos',
            'factor_16': 'Factor-16 No Constitutiva de Renta Acogido a Impto.',
            'factor_17': 'Factor-17 No Constitutiva de Renta de Renta Devolución de Capital Art. 17',
            'factor_18': 'Factor-18 Rentas Extentas de Impro GC Y/O Impto Adicional',
            'factor_19': 'Factor-19 Ingreso no Constitutivos de Renta', 
            'factor_20': 'Factor-20 Sin Derecho a Devolución',
            'factor_21': 'Factor-21 Con Derecho a Devolución',
            'factor_22': 'Factor-22 Sin Derecho a Devolución',
            'factor_23': 'Factor-23 Con Derecho a Devolución',
            'factor_24': 'Factor-24 Sin Derecho a Devolución',
            'factor_25': 'Factor-25 Con Derecho a Devolución',
            'factor_26': 'Factor-26 Sin Derecho a Devolución',
            'factor_27': 'Factor-27 Con Derecho a Devolución',
            'factor_28': 'Factor-28 Credito por IPE',
            'factor_29': 'Factor-29 Sin Derecho a Devolución',
            'factor_30': 'Factor-30 Con Derecho a Devolución',
            'factor_31': 'Factor-31 Sin Derecho a Devolución',
            'factor_32': 'Factor-32 Con Derecho a Devolución',
            'factor_33': 'Factor-33 Credito por IPE',
            'factor_34': 'Factor-34 Cred. Por Impto.',
            'factor_35': 'Factor-35 Tasa Efectiva Del Cred. Del FUT (TEF)',
            'factor_36': 'Factor-36 Tasa Efectiva Del Cred. Del FUNT (TEX)',
            'factor_37': 'Factor-37 Devolución de Capital Art. 17 num 7 LIR',
        }

        todos_los_factores = FACTORES_BASE_UI + FACTORES_CALCULADOS_UI + FACTORES_DIRECTOS_UI
        for nombre_campo in todos_los_factores:
            if nombre_campo in nombres_factores:
                self.fields[nombre_campo] = forms.DecimalField(
                    label=nombres_factores[nombre_campo],
                    required=False,
                    initial=Decimal('0.00'),
                    max_digits=18,
                    decimal_places=8,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'placeholder': '0.00',
                        'step': '0.00000001'
                    })
                )

    def clean(self):
        cleaned_data = super().clean()
        ingreso_por_montos = cleaned_data.get('ingreso_por_montos', False)

        # --- CAMBIO: La validación ahora suma hasta el factor 19 ---
        if not ingreso_por_montos:
            suma_factores_base = Decimal('0.0')
            # Usamos la lista de factores base (8-19)
            for nombre_campo in FACTORES_BASE_UI: 
                valor = cleaned_data.get(nombre_campo)
                if valor:
                    suma_factores_base += valor
            
            if suma_factores_base > Decimal('1.00000001'):
                raise forms.ValidationError(
                    f'Error de validación: La suma de los factores del 8 al 19 ({suma_factores_base}) no puede ser mayor a 1 cuando se ingresan factores.'
                )
        
        return cleaned_data