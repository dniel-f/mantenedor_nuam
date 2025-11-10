from django.shortcuts import render
from .models import Log
from .forms import LogFilterForm
from usuarios.decorators import login_requerido_personalizado, rol_requerido

# ==========================================================
#  VISTA 1: Monitor de Auditoría
# ==========================================================
@login_requerido_personalizado
@rol_requerido(roles_permitidos=['Administrador', 'Auditor'])
def log_list_view(request):
    
    form = LogFilterForm(request.GET or None)
    
    # Queryset base: todos los logs, ordenados por fecha más reciente
    # Usamos select_related para traer los datos del usuario y calificación
    qs = Log.objects.select_related('id_usuario', 'id_calificacion').order_by('-fecha')
    
    if form.is_valid():
        if form.cleaned_data.get('accion'):
            qs = qs.filter(accion=form.cleaned_data['accion'])
            
        if form.cleaned_data.get('id_usuario'):
            qs = qs.filter(id_usuario=form.cleaned_data['id_usuario'])
            
        if form.cleaned_data.get('fecha_desde'):
            qs = qs.filter(fecha__gte=form.cleaned_data['fecha_desde'])
            
        if form.cleaned_data.get('fecha_hasta'):
            qs = qs.filter(fecha__lte=form.cleaned_data['fecha_hasta'])

    context = {
        'form_filtros': form,
        'logs': qs
    }
    
    return render(request, 'auditoria/log_lista.html', context)