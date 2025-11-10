from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Nota: No usamos 'usuarios/login' porque estas son las rutas de la app.
    # El prefijo 'usuarios/' se pondrá en el archivo principal.
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- Rutas del CRUD de Usuarios ---
    path('', views.user_list_view, name='lista_usuarios'),
    path('crear/', views.user_create_view, name='crear_usuario'),
    path('<int:pk>/modificar/', views.user_update_view, name='modificar_usuario'),
]