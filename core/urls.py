from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, signup

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('', include(router.urls)),
    path('signup/', signup),
    path('auth/', include('rest_framework.urls')),
]