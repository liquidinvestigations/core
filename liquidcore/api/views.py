from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, api_view
from rest_framework.views import APIView

from .models import *
from .permissions import IsAdminOrSelf
from .serializers import *

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'

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
        # TODO start/stop service only if needed
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


def _get_setting(name):
    return Setting.objects.get(name=name)

@api_view()
def network_status(request):
    return Response({})

class NetworkDomain(APIView):
    def get(self, request, format=None):
        return Response({"domain": settings.LIQUID_DOMAIN})

    def put(self, request, format=None):
        # TODO NOT IMPLEMENTED
        return Response({"detail": "not implemented"},
                        status=status.HTTP_501_NOT_IMPLEMENTED)

class NetworkLan(APIView):
    def get(self, request, format=None):
        lan = _get_setting('network.lan')
        return Response(lan.data)

    def put(self, request, format=None):
        return Response()

class NetworkWan(APIView):
    def get(self, request, format=None):
        wan = _get_setting('network.wan')
        return Response(wan.data)

    def put(self, request, format=None):
        return Response()

class NetworkSsh(APIView):
    def get(self, request, format=None):
        ssh = _get_setting('network.ssh')
        return Response(ssh.data)

    def put(self, request, format=None):
        return Response()
