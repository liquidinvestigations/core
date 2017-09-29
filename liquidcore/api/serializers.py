from django.contrib.auth.models import User
from rest_framework import serializers

from .models import *

class UserSerializer(serializers.HyperlinkedModelSerializer):
    # rename the is_staff field
    is_admin = serializers.BooleanField(source='is_staff')
    username = serializers.CharField(max_length=150, read_only=True)

    # hyperlink urls using username as identity
    url = serializers.HyperlinkedIdentityField(
        view_name='user-detail',
        lookup_field='username'
    )
    class Meta:
        model = User
        fields = ('url', 'username', 'first_name',
                  'last_name', 'is_admin', 'is_active')

    def validate_username(self, value):
        # TODO: proper validation
        return value

class UserActiveSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        style={'type': 'password'},
        required=False
    )

    def validate_password(self, password):
        # TODO: proper validation
        if len(password) < 8:
            raise serializers.ValidationError(
                    "Password needs to be at least 8 characters long"
            )
        if len(password) > 64:
            raise serializers.ValidationError(
                    "Password cannot be longer than 64 characters"
            )
        return password

class PasswordChangeSerializer(serializers.Serializer):
    old_password = PasswordSerializer(required=False)
    new_password = PasswordSerializer

class ServiceSerializer(serializers.ModelSerializer):
    url = serializers.ReadOnlyField()
    class Meta:
        model = Service
        fields = '__all__'

class ServiceEnabledSerializer(serializers.Serializer):
    is_enabled = serializers.BooleanField()

class NodeSerializer(serializers.ModelSerializer):
    data = serializers.ReadOnlyField()

    class Meta:
        model = Node
        exclude = ('data_text',)

class NodeTrustedSerializer(serializers.Serializer):
    is_trusted = serializers.BooleanField()
