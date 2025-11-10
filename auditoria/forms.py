from django import forms
from usuarios.models import Usuario

# Opciones de ACCION (basadas en lo que se guarda en el Log)
ACCION_CHOICES = (
    ('', '-- Todas las Acciones --'),
    ('INSERT', 'Creación (INSERT)'),
    ('UPDATE', 'Modificación (UPDATE)'),
    ('DELETE', 'Eliminación (DELETE)'),
    ('IMPORT', 'Carga Masiva (IMPORT)'),
)

class LogFilterForm(forms.Form):
    
    accion = forms.ChoiceField(
        choices=ACCION_CHOICES,
        required=False,
        label='Acción',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Filtro por usuario
    id_usuario = forms.ModelChoiceField(
        queryset=Usuario.objects.all(),
        required=False,
        label='Usuario',
        empty_label='-- Todos los Usuarios --',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Filtro por rango de fechas
    fecha_desde = forms.DateField(
        label='Fecha Desde',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    fecha_hasta = forms.DateField(
        label='Fecha Hasta',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )