from django.urls import path
from . import views

# Damos un 'app_name' para evitar colisiones de nombres
app_name = 'auditoria'

urlpatterns = [
    path('', views.log_list_view, name='lista_logs'),


    
]