import re
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import *

def valid_username(username):
    if not username:
        raise serializers.ValidationError("empty username")
    if not bool(re.match(r"^(\w|\.)+$", username)):
        raise serializers.ValidationError("username can only contain letters, digits, underscore and dot")
    if len(username) > 64:
        raise serializers.ValidationError("username too long")
    return username

def valid_password(password):
    if len(password) < 8:
        raise serializers.ValidationError("password too short")
    return password

def valid_domain(domain):
    if not bool(re.match(r"^((\w|-)+\.)+(\w+)$", domain)):
        raise serializers.ValidationError("invalid hostname")
    return domain

class CreateUserSerializer(serializers.HyperlinkedModelSerializer):
    is_admin = serializers.BooleanField(source='is_staff')
    username = serializers.CharField(validators=[valid_username])

    # hyperlink urls using username as identity
    url = serializers.HyperlinkedIdentityField(
        view_name='user-detail',
        lookup_field='username'
    )
    class Meta:
        model = User
        fields = ('url', 'username', 'first_name',
                  'last_name', 'is_admin', 'is_active')

class UpdateUserSerializer(serializers.HyperlinkedModelSerializer):
    # rename the is_staff field
    is_admin = serializers.BooleanField(source='is_staff')
    username = serializers.CharField(read_only=True, validators=[valid_username])

    # hyperlink urls using username as identity
    url = serializers.HyperlinkedIdentityField(
        view_name='user-detail',
        lookup_field='username'
    )
    class Meta:
        model = User
        fields = ('url', 'username', 'first_name',
                  'last_name', 'is_admin', 'is_active')

class UserActiveSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class PasswordChangeSerializer(serializers.Serializer):
    # old_password is not validated, as it's just being passed to check_login
    old_password = serializers.CharField(required=False)
    new_password = serializers.CharField(validators=[valid_password])

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

class NetworkDomainSerializer(serializers.Serializer):
    domain = serializers.CharField(validators=[valid_domain])

class WifiLoginSerializer(serializers.Serializer):
    ssid = serializers.CharField(max_length=31, min_length=1)
    password = serializers.CharField(max_length=63, min_length=8)

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
