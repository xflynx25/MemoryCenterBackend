# urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


# visual router for views, not in production, will be blank otherwise
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='users')

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('home/', views.home, name='home'),
    path('', include(router.urls)),  # <- all the ModelViewSet routes will be under /api/
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]