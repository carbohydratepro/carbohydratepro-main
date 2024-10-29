from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView


urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_transaction, name='create_transaction'),
    path('settings/', views.settings_view, name='settings'),
    path('edit/<int:transaction_id>/', views.edit_transaction, name='edit_transaction'),
    path('delete/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('api/receive-data/', views.receive_data, name='receive_data'),
    path('graph/', views.display_graph, name='display_graph'),
    path('api/sensor-data/', views.get_sensor_data, name='get_sensor_data'),
]