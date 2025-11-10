from rest_framework.routers import DefaultRouter
from .api_views import CalificacionViewSet

#
router = DefaultRouter()
router.register(r'calificaciones', CalificacionViewSet, basename='calificacion')

urlpatterns = router.urls