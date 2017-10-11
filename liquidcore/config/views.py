import fcntl
from contextlib import contextmanager
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
        setting = Setting.objects.get(name=self.setting_name)
        return Response(setting.data)

    def put(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            setting = Setting.objects.get(name=self.setting_name)
            setting.data = serializer.validated_data
            setting.save()
            update_system()
            return Response(serializer.validated_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NetworkDomain(NetworkSettingAPIView):
    setting_name = "domain"
    serializer_class = NetworkDomainSerializer

class NetworkLan(NetworkSettingAPIView):
    setting_name = "lan"
    serializer_class = LanSerializer

class NetworkWan(NetworkSettingAPIView):
    setting_name = "wan"
    serializer_class = WanSerializer

class NetworkSsh(NetworkSettingAPIView):
    setting_name = "ssh"
    serializer_class = SshSerializer

def _get_settings():
    return {s.name: s for s in Setting.objects.all()}

@contextmanager
def _lock():
    with open(settings.INITIALIZE_LOCK_FILE_PATH, 'w') as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)

class Registration(APIView):
    permission_classes=[AllowAny]
    def get(self, request, format=None):
        settings = _get_settings()
        if settings['initialized'].data:
            return Response({"detail": "Registration already done"},
                            status=status.HTTP_400_BAD_REQUEST)
        defaults = {
            "username": "admin",
            "password": "",
            "domain": settings['domain'].data,
            "lan": settings['lan'].data,
            "wan": settings['wan'].data,
            "ssh": settings['ssh'].data,
        }
        return Response(defaults)

    def post(self, request, format=None):
        with _lock():
            settings = _get_settings()
            if settings['initialized'].data:
                return Response({"detail": "Registration already done"},
                                status=status.HTTP_400_BAD_REQUEST)

            # validate and extract the data
            serializer = RegistrationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            for key in ['domain', 'lan', 'wan', 'ssh']:
                setting_name = key
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

            initialized = settings['initialized']
            initialized.data = True
            initialized.save()

        return Response()
