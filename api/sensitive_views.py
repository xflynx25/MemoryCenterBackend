from django.shortcuts import render
from .serializers import CustomUserSerializer
from django.contrib.auth.models import User
from rest_framework import viewsets

# to view, only for development
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    serializer_class = CustomUserSerializer