# en calificaciones/urls.py
from django.urls import path
from . import views

app_name = 'calificaciones'

urlpatterns = [
    
    path('', views.calificacion_list_view, name='lista_calificaciones'),
    
    path('crear/', views.calificacion_create_view, name='crear_calificacion'),

    path('calcular-factores/', views.calcular_factores_view, name='calcular_factores'),

    path('<int:pk>/eliminar/', views.calificacion_delete_view, name='eliminar_calificacion'),

    path('<int:pk>/modificar/', views.calificacion_update_view, name='modificar_calificacion'),  

    path('carga-masiva/', views.calificacion_carga_masiva_view, name='carga_masiva'),
    
    path('exportar-csv/', views.calificacion_export_csv_view, name='exportar_csv'),

    path('carga-masiva-montos/', views.calificacion_carga_montos_view, name='carga_masiva_montos'),
]