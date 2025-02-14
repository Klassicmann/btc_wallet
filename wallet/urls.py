from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('send/', views.send_transaction, name='send_transaction'),
]