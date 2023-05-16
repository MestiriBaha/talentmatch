from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    last_login = serializers.DateTimeField(default=timezone.now)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'last_login']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user