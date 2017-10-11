from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, api_view
from rest_framework.views import APIView
from rest_framework import status

from .models import *
from .serializers import *
from .system import update_system

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    lookup_field = 'username'
    lookup_value_regex = USERNAME_URL_REGEX

    # don't let the user update the `username` field
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateUserSerializer
        return UpdateUserSerializer

    # @list_route creates an endpoint that doesn't contain the pk.
    # We don't return a list, but that's not a problem.
    @list_route(
        methods=['get'],
        permission_classes=[AllowAny],
        url_name='whoami'
    )
    def whoami(sef, request):
        """Gets the current logged in user.
        Marks the result under the key 'is_authenticated'."""

        username = request.user.username
        if not username:
            return Response({"is_authenticated": False})
        queryset = User.objects.get(username=username)
        data = UpdateUserSerializer(queryset, context={'request':request}).data
        data["is_authenticated"] = True
        return Response(data)

    @detail_route(
        methods=['put'],
        permission_classes=[IsAdminUser],
    )
    def active(self, request, username=None):
        """Sets the user as active or inactive"""
        user = self.get_object()

        serializer = UserActiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user.is_active = data['is_active']
        user.save()
        return Response(status=status.HTTP_200_OK)

    @detail_route(
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def password(self, request, username=None):
        user = self.get_object()
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not request.user.is_staff:
            if user != request.user:
                return Response({"detail": "Only admins can change other user's passwords"},
                                status=status.HTTP_403_FORBIDDEN)
            # admin users don't need to specify the old password
            if 'old_password' not in data:
                return Response({"detail": "old_password not specified"},
                                status=status.HTTP_400_BAD_REQUEST)
            if not user.check_password(data['old_password']):
                return Response({"old_password": ["Wrong Password"]},
                                status=status.HTTP_400_BAD_REQUEST)
        user.set_password(data['new_password'])
        user.save()
        return Response(status=status.HTTP_200_OK)


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    @detail_route(
        methods=['put'],
        permission_classes=[IsAdminUser],
    )
    def enabled(self, request, pk=None):
        """Sets the service as enabled or disabled."""
        serializer = ServiceEnabledSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = self.get_object()
        service.is_enabled = data['is_enabled']
        service.save()
        update_system()
        return Response(status=status.HTTP_200_OK)

class NodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer

    @detail_route(
        methods=['put'],
        permission_classes=[IsAdminUser],
    )
    def trusted(self, request, pk=None):
        """Sets the service as enabled or disabled."""
        serializer = NodeTrustedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        node = self.get_object()
        node.is_trusted = data['is_trusted']
        node.save()
        update_system()
        return Response(status=status.HTTP_200_OK)


@api_view()
def network_status(request):
    return Response({})

class NetworkSettingAPIView(APIView):
    def get(self, request, format=None):
        setting, created = Setting.objects.get_or_create(
            name=self.setting_name
        )
        if created:
            setting.data = self.default_data
            setting.save()

        return Response(setting.data)

    def put(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            setting, _ = Setting.objects.get_or_create(name=self.setting_name)
            setting.data = serializer.validated_data
            setting.save()
            update_system()
            return Response(serializer.validated_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NetworkDomain(NetworkSettingAPIView):
    setting_name = "network.domain"
    serializer_class = NetworkDomainSerializer
    default_data = {
        "domain": 'liquidnode.liquid',
    }

class NetworkLan(NetworkSettingAPIView):
    setting_name = "network.lan"
    serializer_class = LanSerializer
    default_data = {
        "ip": "10.0.0.1",
        "netmask": "255.255.255.0",
        "dhcp_range": "10.0.0.100-255",
        "hotspot": {
          "ssid": "",
          "password": ""
        },
        "eth": False,
    }

class NetworkWan(NetworkSettingAPIView):
    setting_name = "network.wan"
    serializer_class = WanSerializer
    default_data = {
        "wifi": {
          "ssid": "",
          "password": "",
        }
    }

class NetworkSsh(NetworkSettingAPIView):
    setting_name = "network.ssh"
    serializer_class = SshSerializer
    default_data = {
        "enabled": False,
        "authorized_keys": [],
        "port": 22,
    }

class Registration(APIView):
    permission_classes=[AllowAny]
    def get(self, request, format=None):
        if Setting.objects.count() > 0:
            return Response({"detail": "Registration already done"},
                            status=status.HTTP_400_BAD_REQUEST)
        defaults = {
            "username": "admin",
            "password": "",
            "domain": NetworkDomain.default_data,
            "lan": NetworkLan.default_data,
            "wan": NetworkWan.default_data,
            "ssh": NetworkSsh.default_data,
        }
        return Response(defaults)

    def post(self, request, format=None):
        if Setting.objects.count() > 0:
            return Response({"detail": "Registration already done"},
                            status=status.HTTP_400_BAD_REQUEST)

        # validate and extract the data
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        for key in ['wan', 'lan', 'ssh']:
            setting_name = "network." + key
            setting = Setting(name=setting_name, data=data[key])
            setting.save()

        # create initial user
        User.objects.create_user(
            username=data['username'],
            password=data['password'],
            is_staff=True,
            is_superuser=True
        )
        update_system()
        return Response()
