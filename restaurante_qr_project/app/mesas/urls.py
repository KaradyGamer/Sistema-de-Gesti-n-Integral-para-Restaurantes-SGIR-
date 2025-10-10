# app/mesas/urls.py
from django.urls import path
from .views import MesaListCreateView

urlpatterns = [
    path('', MesaListCreateView.as_view(), name='lista-mesas'),
]
