from datetime import datetime, timedelta
import pytest
from django.utils.timezone import utc, now
from django_otp.plugins.otp_totp.models import TOTPDevice
from liquidcore.twofactor import invitations, models
from conftest import _totp, is_logged_in, _reset_last_use

pytestmark = pytest.mark.django_db

INVITATION_DURATION = 30  # minutes


@pytest.yield_fixture
def mock_time(monkeypatch):
    class mock_time:
        time = staticmethod(lambda: t.timestamp())
    t = now()
    patch = monkeypatch.setattr
    patch('liquidcore.twofactor.invitations.now', lambda: t)
    patch('django_otp.plugins.otp_totp.models.time', mock_time)

    def set_time(value):
        nonlocal t
        assert t.tzinfo is utc
        t = value

    yield set_time


@pytest.mark.parametrize(
    'minutes,username_ok,password_ok,code_ok,invitation,success',
    [
        (10, True, True, True, True, True),
        (40, True, True, True, False, False),
        (10, False, True, True, True, False),
        (10, True, False, True, True, False),
        (10, True, True, False, True, False),
    ])
def test_flow(
        client, mock_time, minutes, username_ok, password_ok, code_ok,
        invitation, success,
        ):

    t0 = datetime(2016, 6, 13, 12, 0, 0, tzinfo=utc)
    t1 = t0 + timedelta(minutes=minutes)

    mock_time(t0)
    url = invitations.invite('john', INVITATION_DURATION, create=True)
    assert not is_logged_in(client)

    mock_time(t1)
    client.get(url)

    if not invitation:
        assert TOTPDevice.objects.count() == 0
        return

    [device] = TOTPDevice.objects.all()
    hour = timedelta(hours=1)
    resp = client.post(url, {
        'username': 'john' if username_ok else 'ramirez',
        'password': 'secretz',
        'password-confirm': 'secretz' if password_ok else 'foobar',
        'code': _totp(device, t1) if code_ok else _totp(device, t1 + hour),
    })

    if success:
        assert "Verification successful." in resp.content.decode('utf-8')
        assert is_logged_in(client)

    else:
        assert not is_logged_in(client)


def _accept(client, invitation, password, mock_now=None):
    client.get(f'/invitation/{invitation.code}')
    [device] = invitation.user.totpdevice_set.all()

    resp = client.post(f'/invitation/{invitation.code}', {
        'username': invitation.user.username,
        'password': password,
        'password-confirm': password,
        'code': _totp(device, mock_now or now()),
    })
    assert "Verification successful." in resp.content.decode('utf8')

    device.refresh_from_db()
    return device


@pytest.mark.parametrize('username,password,interval,success', [
    ('john', 'pw', timedelta(0), True),
    ('john', 'pw', timedelta(minutes=2), False),
    ('johnny', 'pw', timedelta(0), False),
    ('john', 'pwz', timedelta(0), False),
])
def test_login(client, username, password, interval, success):
    invitations.invite('john', INVITATION_DURATION, create=True)
    device = _accept(client, models.Invitation.objects.get(), 'pw')
    assert is_logged_in(client)
    client.logout()
    _reset_last_use(device)
    assert not is_logged_in(client)
    client.post('/accounts/login/', {
        'username': username,
        'password': password,
        'otp_token': _totp(device, now() + interval),
    })
    if success:
        assert is_logged_in(client)
    else:
        assert not is_logged_in(client)
