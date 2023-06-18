from rest_framework import viewsets
from django.db import models
from rest_framework import serializers

class DummyModel(models.Model):
    pass

class DummySerializer(serializers.ModelSerializer):
    class Meta:
        model = DummyModel
        fields = []

class DummyView(viewsets.ModelViewSet):
    queryset = DummyModel.objects.none()  # Empty queryset
    serializer_class = DummySerializer