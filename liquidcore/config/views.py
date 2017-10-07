from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, api_view
from rest_framework.views import APIView
from rest_framework import status

from .models import *
from .permissions import IsAdminOrSelf
from .serializers import *

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    lookup_field = 'username'

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
        data = UserSerializer(queryset, context={'request':request}).data
        data["is_authenticated"] = True
        return Response(data)

    @detail_route(
        methods=['put'],
        permission_classes=[IsAdminUser],
        url_name='active'
    )
    def set_active(self, request, pk=None):
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
        permission_classes=[IsAdminOrSelf],
        url_name='password'
    )
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not request.user.is_staff:
            # admin users don't need to specify the old password
            if not user.check_password(data['old_password']):
                return Response({"old_password": "Invalid Password"},
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
        url_name='enabled'
    )
    def set_enabled(self, request, pk=None):
        """Sets the service as enabled or disabled."""
        serializer = ServiceEnabledSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = self.get_object()
        service.is_enabled = data['is_enabled']
        service.save()
        # TODO send start/stop command to system
        return Response(status=status.HTTP_200_OK)

class NodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer

    @detail_route(
        methods=['put'],
        permission_classes=[IsAdminUser],
        url_name='trusted'
    )
    def set_trusted(self, request, pk=None):
        """Sets the service as enabled or disabled."""
        serializer = NodeTrustedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        node = self.get_object()
        node.is_trusted = data['is_trusted']
        node.save()
        # TODO send updated node list to the discovery service
        return Response(status=status.HTTP_200_OK)


@api_view()
def network_status(request):
    return Response({})

class NetworkDomain(APIView):
    def get(self, request, format=None):
        return Response({"domain": settings.LIQUID_DOMAIN})

    def put(self, request, format=None):
        serializer = NetworkDomainSerializer(data=request.data)
        if serializer.is_valid():
            # TODO send change domain command to system
            return Response({"detail": "not implemented"},
                            status=status.HTTP_501_NOT_IMPLEMENTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            # TODO send update to system
            return Response(serializer.validated_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NetworkLan(NetworkSettingAPIView):
    setting_name = "network.lan"
    serializer_class = LanSerializer
    default_data = {
        "lan": {
          "ip": "10.0.0.1",
          "netmask": "255.255.255.0",
          "dhcp_range": "10.0.0.100-255",
          "hotspot": {
            "ssid": "",
            "password": ""
          },
          "eth": False
        }
    }

class NetworkWan(NetworkSettingAPIView):
    setting_name = "network.wan"
    serializer_class = WanSerializer
    default_data = {
        "wan": {
          "wifi": {
            "ssid": "",
            "password": ""
          }
        }
    }

class NetworkSsh(NetworkSettingAPIView):
    setting_name = "network.ssh"
    serializer_class = SshSerializer
    default_data = {
        "ssh": {
          "enabled": False,
          "authorized_keys": [],
          "port": 22
        }
    }
