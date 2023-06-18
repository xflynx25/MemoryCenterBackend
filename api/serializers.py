from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            hashed_password = make_password(password)
            instance.password = hashed_password
        instance.save()
        return instance

    def to_representation(self, instance):
        rep = super(UserSerializer, self).to_representation(instance)
        #rep['password'] = "*****" # to hide the password
        return rep
