from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from calificaciones.views import dashboard_view

# --- IMPORTACIONES DE JWT (ACTUALIZADAS) ---
from rest_framework_simplejwt.views import TokenRefreshView
# Importamos NUESTRA vista de login de API desde la app 'usuarios'
from usuarios.views import MyTokenObtainPairView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('calificaciones/', include('calificaciones.urls', namespace='calificaciones')),
    path('auditoria/', include('auditoria.urls', namespace='auditoria')),
    #path('', TemplateView.as_view(template_name="home_temporal.html"), name='home'),
    path('usuarios/', include('usuarios.urls', namespace='usuarios')),

    path('', dashboard_view, name='home'),  # Página principal redirige al dashboard


    # URLs de Autenticación (JWT)
    # --- CAMBIO: Apuntamos a nuestra vista personalizada ---
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/', include('calificaciones.api_urls')),

    
]