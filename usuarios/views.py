from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q # Para búsquedas
from .forms import LoginForm, UserFilterForm, UserForm 
from .models import Usuario, Rol, Estado
from .decorators import login_requerido_personalizado, rol_requerido 

from rest_framework_simplejwt.views import TokenObtainPairView
from .forms import MyTokenObtainPairSerializer

def login_view(request):
    # Si el usuario ya está logueado, lo redirigimos
    if 'id_usuario' in request.session:
        return redirect('home') # 'home' será nuestra futura página principal

    form = LoginForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        # El formulario validó al usuario
        usuario = form.cleaned_data['usuario']
        
        # Guardamos los datos del usuario en la sesión
        request.session['id_usuario'] = usuario.id_usuario
        request.session['nombre_usuario'] = usuario.nombre
        request.session['rol_id'] = usuario.id_rol_id
        
        # Obtenemos el nombre del Rol para mostrarlo
        try:
            rol_nombre = Rol.objects.get(id_rol=usuario.id_rol_id).nombre
            request.session['rol_nombre'] = rol_nombre
        except Rol.DoesNotExist:
            request.session['rol_nombre'] = 'Desconocido'

        messages.success(request, f'¡Bienvenido, {usuario.nombre}!')
        
        # Redirigir a la página principal
        # Crearemos esta URL 'home' en el siguiente paso
        return redirect('home') 
    
    return render(request, 'usuarios/login.html', {'form': form})


def logout_view(request):
    # Limpiamos la sesión
    try:
        del request.session['id_usuario']
        del request.session['nombre_usuario']
        del request.session['rol_id']
        del request.session['rol_nombre']
    except KeyError:
        pass # Si ya estaba deslogueado, no hagas nada

    # request.session.flush() # Alternativa más simple: borra TODO
    
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('usuarios:login') # Lo mandamos de vuelta al login



# ==========================================================
#  VISTA 3: Listar Usuarios (CU6)
# ==========================================================
@login_requerido_personalizado
@rol_requerido(roles_permitidos=['Administrador'])
def user_list_view(request):
    
    form = UserFilterForm(request.GET or None)
    qs = Usuario.objects.select_related('id_rol', 'id_estado').order_by('nombre')
    
    if form.is_valid():
        if form.cleaned_data.get('nombre'):
            # Buscamos en nombre O correo
            qs = qs.filter(
                Q(nombre__icontains=form.cleaned_data['nombre']) |
                Q(correo__icontains=form.cleaned_data['nombre'])
            )
        if form.cleaned_data.get('id_rol'):
            qs = qs.filter(id_rol=form.cleaned_data['id_rol'])
        if form.cleaned_data.get('id_estado'):
            qs = qs.filter(id_estado=form.cleaned_data['id_estado'])

    context = {
        'form_filtros': form,
        'usuarios': qs
    }
    return render(request, 'usuarios/user_list.html', context)


# ==========================================================
#  VISTA 4: Crear Usuario (CU6)
# ==========================================================
@login_requerido_personalizado
@rol_requerido(roles_permitidos=['Administrador'])
def user_create_view(request):
    
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            try:
                # El 'save' del formulario ya hashea la contraseña
                usuario = form.save()
                messages.success(request, f'Usuario "{usuario.nombre}" creado exitosamente.')
                return redirect('usuarios:lista_usuarios')
            except Exception as e:
                messages.error(request, f'Error al crear el usuario: {e}')
    else:
        form = UserForm()
        
    context = {
        'form': form,
        'titulo_pagina': 'Crear Nuevo Usuario'
    }
    return render(request, 'usuarios/user_form.html', context)


# ==========================================================
#  VISTA 5: Modificar Usuario (CU6)
# ==========================================================
@login_requerido_personalizado
@rol_requerido(roles_permitidos=['Administrador'])
def user_update_view(request, pk):
    
    usuario = get_object_or_404(Usuario, id_usuario=pk)
    
    if request.method == 'POST':
        # Pasamos 'instance=usuario' para que sepa que estamos editando
        form = UserForm(request.POST, instance=usuario)
        if form.is_valid():
            try:
                # El 'save' del formulario hashea si la contraseña cambió
                form.save()
                messages.success(request, f'Usuario "{usuario.nombre}" actualizado exitosamente.')
                return redirect('usuarios:lista_usuarios')
            except Exception as e:
                messages.error(request, f'Error al actualizar el usuario: {e}')
    else:
        # Rellenamos el formulario con los datos del usuario
        form = UserForm(instance=usuario)
        
    context = {
        'form': form,
        'titulo_pagina': f'Modificar Usuario: {usuario.nombre}'
    }
    return render(request, 'usuarios/user_form.html', context)

# ==========================================================
#  VISTA 6: Login de API (JWT Personalizado)
# ==========================================================
class MyTokenObtainPairView(TokenObtainPairView):
    """
    Vista de login para la API que usa nuestro serializer personalizado.
    """
    serializer_class = MyTokenObtainPairSerializer