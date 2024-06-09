from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_transaction, name='create_transaction'),
    path('settings/', views.settings_view, name='settings'),
]