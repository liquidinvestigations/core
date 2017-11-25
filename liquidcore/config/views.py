import fcntl
from django.utils import timezone
from contextlib import contextmanager
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.parsers import BaseParser
from rest_framework.renderers import BaseRenderer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, api_view, \
     permission_classes, parser_classes
from rest_framework.views import APIView
from rest_framework import status

from .models import Service, Setting, Node, VPNClientKey
from . import serializers
from .system import reconfigure_system, get_vpn_client_config
from . import agent

OVPN_CONTENT_TYPE = 'application/x-openvpn-profile'

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    lookup_field = 'username'
    lookup_value_regex = serializers.USERNAME_URL_REGEX

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
        data = serializers.UserSerializer(request.user, context={'request':request}).data
        data["is_authenticated"] = True
        return Response(data)

    @detail_route(
        methods=['put'],
        permission_classes=[IsAdminUser],
    )
    def active(self, request, username=None):
        """Sets the user as active or inactive"""
        user = self.get_object()

        serializer = serializers.UserActiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user.is_active = data['is_active']
        user.save()
        return Response()

    @detail_route(
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def password(self, request, username=None):
        user = self.get_object()
        serializer = serializers.PasswordChangeSerializer(data=request.data)
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
        return Response()


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all()
    serializer_class = serializers.ServiceSerializer
    permission_classes = [IsAuthenticated]

    @detail_route(
        methods=['put'],
        permission_classes=[IsAdminUser],
    )
    def enabled(self, request, pk=None):
        """Sets the service as enabled or disabled."""
        serializer = serializers.IsEnabledSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = self.get_object()
        service.is_enabled = data['is_enabled']
        service.save()
        reconfigure_system()
        return Response()

@api_view()
def node_list(request):
    from ..home import discover
    nodes = discover.get_node_list()
    for id, node in enumerate(nodes, 1):
        node['id'] = id
        node['is_trusted'] = True
    return Response(nodes)

@api_view()
def network_status(request):
    return Response({})

class NetworkSettingAPIView(APIView):

    @staticmethod
    def to_db(value):
        return value

    @staticmethod
    def from_db(value):
        return value

    def get(self, request, format=None):
        setting = Setting.objects.get(name=self.setting_name)
        return Response(self.from_db(setting.data))

    def put(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            setting = Setting.objects.get(name=self.setting_name)
            setting.data = self.to_db(serializer.validated_data)
            setting.save()
            reconfigure_system()
            return Response(serializer.validated_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NetworkDomain(NetworkSettingAPIView):
    setting_name = "domain"
    serializer_class = serializers.NetworkDomainSerializer

    @staticmethod
    def to_db(value):
        return value["domain"]

    @staticmethod
    def from_db(value):
        return {"domain": value}

class NetworkLan(NetworkSettingAPIView):
    setting_name = "lan"
    serializer_class = serializers.LanSerializer

class NetworkWan(NetworkSettingAPIView):
    setting_name = "wan"
    serializer_class = serializers.WanSerializer

class NetworkSsh(NetworkSettingAPIView):
    setting_name = "ssh"
    serializer_class = serializers.SshSerializer

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
            serializer = serializers.RegistrationSerializer(data=request.data)
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
            reconfigure_system()

            initialized = settings['initialized']
            initialized.data = True
            initialized.save()

        return Response()

class OVPNRenderer(BaseRenderer):
    media_type = OVPN_CONTENT_TYPE
    format = 'ovpn'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data

class VPNClientKeyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VPNClientKey.objects.all()
    serializer_class = serializers.VPNClientKeySerializer
    lookup_field = 'id'
    lookup_value_regex = r'[1-9][0-9]*'

    @list_route(
        methods=['post'],
        permission_classes=[IsAdminUser],
        url_name='generate'
    )
    def generate(sef, request):
        serializer = serializers.VPNClientKeyLabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        label = serializer.validated_data['label']
        client_key = VPNClientKey.objects.create(label=label)
        serialized_client_key = serializers.VPNClientKeySerializer(client_key)
        reconfigure_system()
        return Response(data=serialized_client_key.data)

    @detail_route(
        methods=['post'],
        permission_classes=[IsAdminUser],
        url_name='revoke'
    )
    def revoke(self, request, id=None):
        serializer = serializers.VPNClientKeyRevokeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_key = self.get_object()
        client_key.revoked = True
        client_key.revoked_reason = serializer.validated_data['revoked_reason']
        client_key.revoked_at = timezone.now()
        client_key.revoked_by = request.user
        client_key.save()

        reconfigure_system()
        return Response()

    @detail_route(
        methods=['get'],
        permission_classes=[IsAdminUser],
        renderer_classes=[OVPNRenderer],
        url_name='download'
    )
    def download(self, request, id=None):
        ovpn_content = get_vpn_client_config(id)
        filename = 'client-key-{}.ovpn'.format(id)
        response = Response(ovpn_content, content_type=OVPN_CONTENT_TYPE)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response

@api_view(['GET'])
@permission_classes([IsAdminUser])
def vpn_status(request):
    def get_description(state):
        if state['error_message']:
            return 'Error.'
        if not state['is_enabled']:
            return "Disabled."
        if state['is_running']:
            return 'Up and running.'
        else:
            return 'Starting...'

    vpn_setting = Setting.objects.get(name='vpn')
    status = vpn_setting.data
    # TODO get these with system calls
    status['client']['is_running'] = False
    status['server']['is_running'] = False
    status['server']['registered_key_count'] = VPNClientKey.objects.count()
    status['server']['active_connection_count'] = 0

    status['client']['state_description'] = get_description(status['client'])
    status['server']['state_description'] = get_description(status['server'])
    return Response(status)

def _vpn_set_enabled(module, enabled):
    """Sets the VPN server/client as enabled or disabled.
    module -- one of "server" or "client"
    enabled -- True or False
    """
    vpn_setting = Setting.objects.get(name='vpn')
    vpn = vpn_setting.data
    vpn[module]['is_enabled'] = enabled
    vpn_setting.data = vpn
    vpn_setting.save()

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def vpn_server_enabled(request):
    serializer = serializers.IsEnabledSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    enabled = serializer.validated_data['is_enabled']
    _vpn_set_enabled('server', enabled)
    reconfigure_system()
    return Response()

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def vpn_client_enabled(request):
    serializer = serializers.IsEnabledSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    enabled = serializer.validated_data['is_enabled']
    _vpn_set_enabled('client', enabled)
    reconfigure_system()
    return Response()

class OVPNParser(BaseParser):
    media_type = OVPN_CONTENT_TYPE

    def parse(self, stream, media_type=None, parser_context=None):
        """Simply return a string representing the body of the request."""
        return stream.read()

@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([OVPNParser])
def vpn_client_upload(request):
    ovpn_content = request.data.decode('latin1')
    setting = Setting.objects.get(name='vpn_client_config')
    setting.data = ovpn_content
    setting.save()
    reconfigure_system()
    return Response(data={'detail': 'Upload done.'})

@api_view(['GET'])
@permission_classes([IsAdminUser])
def configure_status(request):
    job_status = agent.status()
    pending = any(
        properties.get('options')
        for properties in job_status['jobs'].values()
    )

    if job_status['is_broken']:
        return Response({
            'status': 'broken',
            'detail': "Configuration is broken.",
        })
    elif pending:
        status = 'configuring'
        return Response({
            'status': 'configuring',
            'detail': "System is reconfiguring.",
        })
    else:
        return Response({
            'status': 'ok',
            'detail': "Configuration finished.",
        })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def configure_repair(request):
    reconfigure_system(repair=True)
    return Response({
        'status': 'ok',
        'detail': "Repair job started.",
    })
