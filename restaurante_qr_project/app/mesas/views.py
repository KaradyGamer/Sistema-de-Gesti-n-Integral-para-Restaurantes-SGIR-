from django.shortcuts import render
# app/mesas/views.py
from rest_framework import generics
from .models import Mesa
from .serializers import MesaSerializer

class MesaListCreateView(generics.ListCreateAPIView):
    queryset = Mesa.objects.all()
    serializer_class = MesaSerializer

# Create your views here.
