"""
Interfaces with portal.adtpulse.com.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/alarm_control_panel.adtpulse/
"""

import json
#from json.decoder import JSONDecodeError
import os
import pickle
from bs4 import BeautifulSoup
from dateutil.parser import parse
import requests
from requests.auth import AuthBase

import logging

import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

"""
Interact with portal.adtpulse.com
"""

class LoginException(Exception):
    """
    Raise when we are unable to log in to portal.adtpulse.com
    """
    pass


class SystemArmedError(Exception):
    """
    Raise when the system is already armed and an attempt to arm it again is made.
    """
    pass

class SystemDisarmedError(Exception):
    """
    Raise when the system is already disamred and an attempt to disarm the system is made.
    """
    pass
   
class ElementException(Exception):
    """
    Raise when we are unable to locate an element on the page.
    """
    pass

class Adtpulse(object):
    """
    Access to ADT Pulse partners and accounts.
    This class is used to interface with the options available through
    portal.adtpulse.com. The basic functions of checking system status and arming
    and disarming the system are possible.
    """

    """
    ADT Pulse constants
    """
    COOKIE_PATH = './adtpulse_cookies.pickle'
    ADTPULSE_JSON_PREAMBLE_SIZE = 18
    DEFAULT_LOCALE = 'en_US'
    HTML_PARSER = 'html.parser'
    ERROR_FIND_TAG = 'div'
    ERROR_FIND_ATTR = {'id': 'warnMsgContents'}
    VALUE_ATTR = 'value'
    ATTRIBUTION = 'Information provided by portal.adtpulse.com'
    
    # ADT Pulse baseURL
    ADTPULSE_DOMAIN = 'https://portal.adtpulse.com'

    """
    Determine the current code version used on portal.adtpulse.com
    """
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


    # Page elements on portal.adtpulse.com that are needed
    # Using a dict for the attributes to set whether it is a name or id for locating the field
    ADTPULSE_CONTEXT_PATH = adtpulse_version(ADTPULSE_DOMAIN)
    LOGIN_URL = ADTPULSE_DOMAIN + ADTPULSE_CONTEXT_PATH + '/access/signin.jsp'
    SUMMARY_URL = ADTPULSE_DOMAIN + ADTPULSE_CONTEXT_PATH + '/summary/summary.jsp'

    STATUS_IMG = ('span', class_='pp_orbStateImage)
    
##   BTN_DISARM = ('id', 'ctl00_phBody_butDisarm')
##   BTN_ARM_STAY = ('id', 'ctl00_phBody_butArmStay', 'ctl00_phBody_ArmingStateWidget_btnArmOptionStay')
##   BTN_ARM_AWAY = ('id', 'ctl00_phBody_butArmAway', 'ctl00_phBody_ArmingStateWidget_btnArmOptionAway')

    def _save_cookies(requests_cookiejar, filename):
        """Save cookies to a file."""
        with open(filename, 'wb') as handle:
            pickle.dump(requests_cookiejar, handle)

    def _load_cookies(filename):
        """Load cookies from a file."""
        with open(filename, 'rb') as handle:
            return pickle.load(handle)

    def _parsed_date(date):
        """Parse a date."""
        return str(parse(date).date()) if date else ''

    def get_session(self, username, password, cookie_path=COOKIE_PATH):
        """Get ADTPULSE HTTP session."""
        class ADTPULSEAuth(AuthBase):  # pylint: disable=too-few-public-methods
            """ADTPULSE authorization storage."""

            def get_session(self, hass, name, username, password, cookie_path):
                """Init."""
                self.username = username
                self.password = password
                self.cookie_path = cookie_path
                if not self._login():
                    raise LoginException('Unable to login to portal.adtpulse.com')

            def __call__(self, r):
                """Call is no-op."""
                return r

        session = requests.session()
        session.auth = ADTPULSEAuth(username, password, cookie_path)
        if os.path.exists(cookie_path):
            session.cookies = _load_cookies(cookie_path)
        else:
            _login(session, cookie_path)
        return session

    def _login(session, cookie_path=COOKIE_PATH, username, password):
        """Login to ADTPULSE."""
        resp = session.get(LOGIN_URL + '?usernameForm=' + username + '&passwordForm=' + password)
        parsed = BeautifulSoup(resp.text, HTML_PARSER)
        resp = session.post(LOGIN_URL, {
            'usernameForm': username,
            'passwordForm': password,
        })
        parsed = BeautifulSoup(resp.text, HTML_PARSER)
        error = parsed.find(ERROR_FIND_TAG, ERROR_FIND_ATTR).string
        if error:
            raise LoginException(error.strip())
        _save_cookies(session.cookies, cookie_path)


    def authenticated(function):
        """Re-authenticate if session expired."""
        def wrapped(*args):
            """Wrap function."""
            try:
                return function(*args)
            except LoginException:
                _login(*args)
                return function(*args)
        return wrapped


    @authenticated
    def get_alarmstatus(session):
        """Get alarm status."""
        resp = session.get(SUMMARY_URL)
        parsed = BeautifulSoup(resp.content, HTML_PARSER)
        alarm_status = parsed.find('span', 'p_boldNormalTextLarge')
        for string in alarm_status.strings:
            if "." in string:
                param, value = string.split(".",1)
            adtpulse_alarmstatus = param
            state = adtpulse_alarmstatus
        return(state)
