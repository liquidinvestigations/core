import re
from collections import OrderedDict
from django.contrib.auth.models import User
from rest_framework import serializers


from . import models

USERNAME_URL_REGEX = r'([a-zA-Z0-9_]|\.)+'
USERNAME_REGEX = r"^{}$".format(USERNAME_URL_REGEX)
DOMAIN_REGEX = r"^(([a-zA-Z0-9]|-)+\.)+([a-zA-Z0-9]+)$"

def valid_username(username):
    if not username:
        raise serializers.ValidationError("empty username")
    if not bool(re.match(USERNAME_REGEX, username)):
        raise serializers.ValidationError("username can only contain letters, digits, underscore and dot")
    if len(username) < 3:
        raise serializers.ValidationError("username too short")
    if len(username) > 64:
        raise serializers.ValidationError("username too long")
    return username

def valid_password(password):
    if len(password) < 8:
        raise serializers.ValidationError("password too short")
    return password

def valid_domain(domain):
    if not bool(re.match(DOMAIN_REGEX, domain)):
        raise serializers.ValidationError("invalid hostname")
    return domain

class UserSerializer(serializers.HyperlinkedModelSerializer):
    is_admin = serializers.BooleanField(source='is_staff')
    username = serializers.CharField(validators=[valid_username])

    # hyperlink urls using username as identity
    url = serializers.HyperlinkedIdentityField(
        view_name='user-detail',
        lookup_field='username'
    )

    def update(self, instance, validated_data):
        if instance.username != validated_data['username']:
            raise serializers.ValidationError("username cannot be changed")
        return super().update(instance, validated_data)

    class Meta:
        model = User
        fields = ('url', 'username', 'first_name',
                  'last_name', 'is_admin', 'is_active')

class UserCreateSerializer(UserSerializer):
    password = serializers.CharField(validators=[valid_password],
        required=False)

    class Meta:
        model = UserSerializer.Meta.model
        fields = UserSerializer.Meta.fields + ('password',)

class UserActiveSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class PasswordChangeSerializer(serializers.Serializer):
    # old_password is not validated, as it's just being passed to check_login
    old_password = serializers.CharField(required=False)
    new_password = serializers.CharField(validators=[valid_password])

class ServiceSerializer(serializers.ModelSerializer):
    url = serializers.ReadOnlyField()

    class Meta:
        model = models.Service
        fields = '__all__'

class IsEnabledSerializer(serializers.Serializer):
    is_enabled = serializers.BooleanField()

class NodeSerializer(serializers.ModelSerializer):
    data = serializers.ReadOnlyField()
    is_trusted = serializers.BooleanField(default=False, source='trusted')
    hostname = serializers.CharField(source='name')

    class Meta:
        model = models.Node
        fields = ['id', 'is_trusted', 'hostname', 'data']

class NodeTrustedSerializer(serializers.Serializer):
    is_trusted = serializers.BooleanField()

class NetworkDomainSerializer(serializers.Serializer):
    domain = serializers.CharField(validators=[valid_domain])

class WifiLoginSerializer(serializers.Serializer):
    ssid = serializers.CharField(max_length=31, min_length=0)  # should be 1
    password = serializers.CharField(max_length=63, min_length=0)  # should be 8

class LanSerializer(serializers.Serializer):
    ip = serializers.IPAddressField(protocol="IPv4")
    netmask = serializers.IPAddressField(protocol="IPv4")
    dhcp_range = serializers.CharField()
    hotspot = WifiLoginSerializer()
    eth = serializers.BooleanField()

class WanSerializer(serializers.Serializer):
    class WanStatic(serializers.Serializer):
        ip = serializers.IPAddressField(protocol="IPv4")
        netmask = serializers.IPAddressField(protocol="IPv4")
        gateway = serializers.IPAddressField(protocol="IPv4")
        dns_server = serializers.IPAddressField(protocol="IPv4")

    wifi = WifiLoginSerializer()
    static = WanStatic(required=False)

class SshSerializer(serializers.Serializer):
    class Key(serializers.Serializer):
        key = serializers.CharField()

    enabled = serializers.BooleanField()
    port = serializers.IntegerField(max_value=65535, min_value=1)
    authorized_keys = Key(many=True)

class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(validators=[valid_username])
    password = serializers.CharField(validators=[valid_password])
    domain = serializers.CharField(validators=[valid_domain])
    lan = LanSerializer()
    wan = WanSerializer()
    ssh = SshSerializer()

class VPNClientKeySerializer(serializers.ModelSerializer):
    revoked_by = serializers.ReadOnlyField(source='revoked_by.username')
    def to_representation(self, instance):
        """Omit blank and null fields from the model"""
        result = super().to_representation(instance)
        return OrderedDict([
                (key, result[key])
                for key in result
                if result[key] not in ['', None]
        ])

    class Meta:
        model = models.VPNClientKey
        fields = '__all__'

class VPNClientKeyLabelSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=255)

class VPNClientKeyRevokeSerializer(serializers.Serializer):
    revoked_reason = serializers.CharField(max_length=255)
