# urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


# visual router for views, not in production, will be blank otherwise
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='users')

urlpatterns = [
    # browsing-mode
    path('view_profile/', views.view_profile, name='view_profile'), #for self
    path('view_profile/<int:user_id>/', views.view_profile, name='view_profile'), #for others
    path('edit_profile/', views.edit_profile, name='edit_profile'), #for self
    path('get_all_items/', views.get_all_items, name='get_all_items'), #for self, or public if others
    path('get_all_topics/', views.get_all_topics, name='get_all_topics'), #for self, or public if others
    path('get_all_collections/', views.get_all_collections, name='get_all_collections'), #for self, or public if others

    # creation-mode
    path('create_collection/', views.create_collection, name='create_collection'),
    path('create_topic/', views.create_topic, name='create_topic'),
    path('edit_topics_in_collection/', views.edit_topics_in_collection, name='edit_topics_in_collection'), #could be own or others topics, maybe shouldn't be plural
    path('add_items_to_topic/', views.add_items_to_topic, name='add_items_to_topic'), 
    path('edit_items_in_topic/', views.edit_items_in_topic, name='edit_items_in_topic'), 

    # study-mode
    path('fetch_n_from_collection/', views.fetch_n_from_collection, name='fetch_n_from_collection'), #send to client next cards to study
    path('update_n_items_user/', views.update_n_items_user, name='update_n_items_user'), #send back over the scores

    # the difficult ones, will be changing visibilities, and adding global collections/topics into your sets. Because of the manual cascading


    # authentication
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # home
    path('home/', views.home, name='home'),

    # default
    path('', include(router.urls)),  # <- all the ModelViewSet routes will be under /api/
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]