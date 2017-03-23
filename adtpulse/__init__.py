"""My ADTPULSE interface."""

import os.path
import pickle
from bs4 import BeautifulSoup
from dateutil.parser import parse
import requests
from requests.auth import AuthBase


HTML_PARSER = 'html.parser'
LOGIN_FORM_TAG = 'form'
LOGIN_FORM_ATTRS = {'name': 'theform'}
STATE_ALARM_TAG = 'div'
STATE_ALARM_ATTRS = 'divOrbTextSummary'

ERROR_FIND_TAG = 'div'
ERROR_FIND_ATTR = {'id': 'warnMsgContents'}

ADTPULSE_DOMAIN = 'https://portal.adtpulse.com'

def adtpulse_version(ADTPULSE_DOMAIN):
    """Determine current ADT Pulse version"""
    resp = requests.get(ADTPULSE_DOMAIN)
    parsed = BeautifulSoup(resp.content, HTML_PARSER)
    adtpulse_script = parsed.find_all('script', type='text/javascript')[4].string
    if "=" in adtpulse_script:
        param, value = adtpulse_script.split("=",1)
    adtpulse_version = value
    adtpulse_version = adtpulse_version[1:-2]
    return(adtpulse_version)

ADTPULSE_CONTEXT_PATH = adtpulse_version(ADTPULSE_DOMAIN)
#print(ADTPULSE_CONTEXT_PATH)
LOGIN_URL = ADTPULSE_DOMAIN + ADTPULSE_CONTEXT_PATH + '/access/signin.jsp'
#print(LOGIN_URL)
DASHBOARD_URL = ADTPULSE_DOMAIN + ADTPULSE_CONTEXT_PATH + '/summary/summary.jsp'
#print(DASHBOARD_URL)

cookie_path = './adtpulse_cookies.pickle'
ATTRIBUTION = 'Information provided by portal.adtpulse.com'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/41.0.2228.0 Safari/537.36'


class ADTPULSEError(Exception):
    """ADTPULSE error."""

    pass


def _save_cookies(requests_cookiejar, filename):
    """Save cookies to a file."""
    with open(filename, 'wb') as handle:
        pickle.dump(requests_cookiejar, handle)


def _load_cookies(filename):
    """Load cookies from a file."""
    with open(filename, 'rb') as handle:
        return pickle.load(handle)


def _get_elem(response, tag, attr):
    """Get element from a response."""
    parsed = BeautifulSoup(response.text, HTML_PARSER)
    return parsed.find(tag, attr)


def _require_elem(response, tag, attrs):
    """Require that an element exist."""
    login_form = _get_elem(response, LOGIN_FORM_TAG, LOGIN_FORM_ATTRS)
    if login_form is not None:
        raise ADTPULSEError('Not logged in')
    elem = _get_elem(response, tag, attrs)
    if elem is None:
        raise ValueError('No element found')
    return elem

### Replace with IF cookie not found ###
def _get_token(session):
    """Get login token."""
    form = _get_elem(session.get(DASHBOARD_URL), ERROR_FIND_TAG, ERROR_FIND_ATTR)
    token_elem = token_elem.get(value)
    print(token_elem)
    if not token_elem:
        token_elem.value = 'Existing login token found'
        return token_elem.get('value')
    raise ADTPULSEError('No login token found')


def _login(session):
    """Login."""
    token = _get_token(session)
    print(token)
    resp = session.post(DASHBOARD_URL)
    if token is not None:
        raise ADTPULSEError('authentication failed')
    error = _get_elem(session.post(LOGIN_URL, {
        'usernameForm': session.auth.username,
        'passwordForm': session.auth.password
    }), ERROR_TAG, ERROR_ATTRS)
    if error is not None:
        raise ADTPULSEError(error.text.strip())
    _save_cookies(session.cookies, session.auth.cookie_path)


def authenticated(function):
    """Re-authenticate if session expired."""
    def wrapped(*args):
        """Wrap function."""
        try:
            return function(*args)
        except ADTPULSEError:
            _login(*args)
            return function(*args)
    return wrapped


@authenticated
def get_alarmstatus(SUMMARY_URL):
    """Determine current ADT Pulse Alarm Status"""
    alarm_status = _require_elem(session.get(SUMMARY_URL), STATE_ALARM_TAG, STATE_ALARM_ATTRS)
    data = {}
    for row in alarm_status.find('span'):
        data[row[0].text.strip().lower().replace(' ', '_')] = row[1].text.strip()
    return data


@authenticated
#def set_alarmstatus(session):
#    """Get package data."""


def get_session(username, password, cookie_path):
    """Get session, existing or new."""
    class ADTPULSEAuth(AuthBase):  # pylint: disable=too-few-public-methods
        """ADTPULSE authorization storage."""

        def __init__(self, username, password, cookie_path):
            """Init."""
            self.username = username
            self.password = password
            self.cookie_path = cookie_path

        def __call__(self, r):
            """Call is no-op."""
            return r

    session = requests.session()
    session.auth = ADTPULSEAuth(username, password, cookie_path)
    session.headers.update({'User-Agent': USER_AGENT})
    if os.path.exists(cookie_path):
        session.cookies = _load_cookies(cookie_path)
    return session
