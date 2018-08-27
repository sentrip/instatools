"""
Instagram Session class provides bare minimum to make
authenticated, rate_limited requests to the Instagram API
"""
from contextlib import contextmanager
from datetime import datetime
from hashlib import md5, sha256
from threading import Lock
from ratelimiter import RateLimiter
from urllib.parse import quote, urljoin
import calendar
import hmac
import json
import logging
import os
import re
import requests
import time
import uuid


logger = logging.getLogger('instagram')
_log = logger._log


def _make_logger(username):
    """Create a logger that prefixes messages with time and username"""
    def patched_log(level, msg, *args, **kwargs):
        time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        id_str = '[%s - %-30s] ' % (time_str, username)
        _log(level, id_str + msg, *args, **kwargs)

    logger._log = patched_log
    return logger


API_VERSION = 'v1'
BASE_URL = 'https://i.instagram.com/api/%s/' % API_VERSION
DEVICE_SETTINGS = {'man': 'Xiaomi', 'model': 'HM 1SW', 'ver': 18, 'rel': '4.3'}
IG_SIG_KEY = '4f8732eb9ba7d1c8e8897a75d6474d4eb3f5279137431b2aafb71fafe2abe178'
USER_AGENT = 'Instagram 10.26.0 Android ({ver}/{rel}; 320dpi; 720x1280; ' \
             '{man}; {model}; armani; qcom; en_US)'.format(**DEVICE_SETTINGS)
HEADERS = {
    'Connection': 'close', 'Accept': '*/*', 'Cookie2': '$Version=1',
    'Accept-Language': 'en-US', 'User-Agent': USER_AGENT,
    'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}


def generate_device_id(seed):
    """Generate new device id"""
    m = md5()
    m.update(seed.encode('utf-8') + '12345'.encode('utf-8'))
    return 'android-' + m.hexdigest()[:16]


def generate_signature(data):
    """
    Generates signed signature of POST data using SIG_KEY (signing key)
    :param data: dict: POST data
    :return: str: data to append to request url
    """
    signature = hmac.new(
        IG_SIG_KEY.encode('utf-8'), data.encode('utf-8'), sha256
    ).hexdigest()
    return 'ig_sig_key_version=4&signed_body=' + signature + '.' + quote(data)


def generate_upload_id():
    """
    Generate new upload id
    :return:
    """
    return str(calendar.timegm(datetime.utcnow().utctimetuple()))


def generate_uuid(typ):
    """
    Generate new uuid
    :param typ:
    :return:
    """
    generated_uuid = str(uuid.uuid4())
    return generated_uuid if typ else generated_uuid.replace('-', '')


class Session:
    """
    Class representing the request-making Session of a single Instagram user
    """
    exponential_sleep_increase = 2
    requests_to_break = 10
    relog_after_failed = 5
    sleep_on_break = 600
    sleep_on_page = 0.5

    _cookies = None
    device_id = None
    password = None
    token = None
    uuid = None
    username = None
    username_id = None

    _session_class = requests.Session

    paths = {
        # Login endpoints
        'login_challenge': 'si/fetch_headers/',
        'login': 'accounts/login/',
        'logout': 'accounts/logout/',
        # Account endpoints
        'profile': 'accounts/current_user/',
        'edit_profile': 'accounts/edit_profile/',
        'change_password': 'accounts/change_password/',
        'change_profile_picture': 'accounts/change_profile_picture/',
        'remove_profile_picture': 'accounts/remove_profile_picture/',
        'set_public': 'accounts/set_public/',
        'set_private': 'accounts/set_private/',
        'set_phone_name': 'accounts/set_phone_and_name/',
        # User endpoints
        'pending': 'friendships/pending',
        'following': 'friendships/{}/following',
        'followers': 'friendships/{}/followers',
        'follow': 'friendships/create/{}/',
        'unfollow': 'friendships/destroy/{}/',
        'block': 'friendships/block/{}/',
        'unblock': 'friendships/unblock/{}/',
        'approve': 'friendships/approve/{}/',
        'ignore': 'friendships/ignore/{}/',
        # Post endpoints
        'like': 'media/{}/like/',
        'unlike': 'media/{}/unlike/',
        'comment': 'media/{}/comment/',
        'remove_comment': 'media/{}/comment/{}/delete/',
        'create_post': '',  # todo add post
        'remove_post': 'media/{}/delete/',
        'save': 'media/{}/save/',
        'unsave': 'media/{}/unsave/',
        'remove_tag': 'media/{}/remove/',
        # Data endpoints
        'comments': 'media/{}/comments/',
        'friendship': 'friendships/show/{}/',
        'geo_media': 'maps/user/{}',
        'likers': 'media/{}/likers/',
        'post': 'media/{}/info/',
        'story': 'feed/user/{}/reel_media',
        'user': 'users/{}/info/',
        'username': 'users/{}/usernameinfo',
        # Feed endpoints
        'location_feed': 'feed/location/{}/',
        'tag_feed': 'feed/tag/{}/',
        'user_feed': 'feed/user/{}/',
        'user_tags': 'usertags/{}/feed',
        'popular': 'feed/popular',
        'timeline': 'feed/timeline',
        'liked': 'feed/liked',
        'saved': 'feed/saved',
        # Search endpoints
        'facebook_search': 'fbsearch/topsearch',
        'location_search': 'fbsearch/places',
        'tag_search': 'tags/search',
        'user_search': 'users/search',
        # Upload
        'configure': 'media/configure',
        'expose': 'qe/expose',
        'upload_photo': 'upload/photo',
        'upload_video': 'upload/video',
        # Other
        'direct_link': 'direct_v2/threads/broadcast/link/',
        'direct_message': 'direct_v2/threads/broadcast/text/',
        'direct_share': 'direct_v2/threads/broadcast/media_share/',
        'direct_threads': 'direct_v2/threads/{}/',
        'explore': 'discover/explore',
        'inbox': 'direct_v2/inbox',
        'share_inbox': 'direct_share/inbox',
        'recent_activity': 'news/inbox',
        'recent_following_activity': 'news',
        'megaphone': 'megaphone/log',
        'autocomplete_users': 'friendships/autocomplete_user_list'
    }

    def __init__(self, username=None, password=None, session=None):

        self._session = self._session_class()
        self._session.headers.update(HEADERS)

        self.setup(username, password, session)

        self.logger = _make_logger(self.username)
        self.hold_requests = Lock()
        self._mutex = Lock()

        # todo add path regex
        self.limits = {
            'a': RateLimiter(100, 3600),  # login/logout
            'b': RateLimiter(60, 3600),  # like/follow/comment
            '.*': RateLimiter(5000, 3600)  # all other requests
        }

    @property
    def rank_token(self):
        return "%s_%s" % (self.username_id, self.uuid)

    @property
    def session_data(self):
        return {
            'device_id': self.device_id,
            'uid': self.username_id,
            'uuid': self.uuid,
            'token': self.token,
            'cookies': self._cookies
        }

    def login_data(self, cookies):
        """
        Using cookies provided,
        gives data to send to Instagram for login approval
        :param cookies: cookies from login challenge
        :return: dict: data to use for login
        """
        return {
            'username': self.username,
            'password': self.password,
            'device_id': self.device_id,
            'guid': self.uuid,
            'phone_id': generate_uuid(True),
            'login_attempt_count': '0',
            '_csrftoken': cookies['csrftoken']
        }

    def login(self):
        """Login to Instagram with account credentials provided in __init__"""
        if self.password is None:
            self.logger.error('Password required for login')
            return False

        # Get login challenge
        resp = self.request('GET', self.url('login_challenge'),
                            return_json=False,
                            params={
                                'challenge_type': 'signup',
                                'guid': generate_uuid(False)
                            })
        if resp.status_code != 200:
            self.logger.error('Requesting login challenge failed')
            return False

        self.logger.debug('Successfully requested login challenge url')
        # Attempt to login with cookies from challenge
        resp = self.request('POST', self.url('login'),
                            return_json=False,
                            data=self.login_data(resp.cookies))

        if resp.status_code != 200:
            self.logger.error('Login POST failed')
            return False

        self.logger.debug('Successfully POSTED to login url')
        self._cookies = {ck.name: ck.value for ck in resp.cookies}

        # Set user data to response data if successful
        data = resp.json()
        if 'logged_in_user' in data:
            self.username_id = data["logged_in_user"]["pk"]
            self.token = self._cookies["csrftoken"]
            self.logger.info('Login success')
            return data['logged_in_user']
        self.logger.info('Login failed')
        return False

    def logout(self):
        """Logout of currently logged-in account"""
        resp = self.request('GET', self.url('logout'), return_json=False)
        if resp.status_code == 200:
            self.token = None
            self.logger.info('Logged out')
            return True
        self.logger.error('Logout failed')
        return False

    def switch_user(self, username=None, password=None, session=None):
        """Switches current account username and password - requires login"""
        self.setup(username, password, session)
        self.logger.info('Switching to user %s', self.username)

    def request(self, method, url, *,
                params=None, data=None, return_json=True, **kwargs):
        """

        :param method:
        :param url:
        :param params:
        :param data:
        :param return_json:
        :param kwargs:
        :return:
        """
        if method == 'GET' and 'friendship' in url:
            params = params or {}
            params.update(ig_sig_key_version=4, rank_token=self.rank_token)

        elif method == 'POST' and isinstance(data, dict):
            dct = data.copy()
            dct.update(_uuid=self.uuid, _uid=self.username_id,
                       _csrftoken=self.token)
            data = generate_signature(json.dumps(dct))

        # Request patching for specific endpoints
        kwargs.update(params=params, data=data)
        # Wait until allowed to request given url
        with self.wait_limit(url):
            # Yay thread safety!
            with self._mutex:
                resp = self._session.request(method, url, **kwargs)

        return resp.json() if return_json else resp

    def request_safely(self, *args, max_attempts=0, **kwargs):
        """
        Make a safe request that returns correct results or dies trying!
        Keeps requesting with exponential back-off until `requests_to_break` is
        reached, at which point each consecutive request is circuit-broken and
        waits `sleep_on_break` seconds until a successful request is made, or
        until `relog_after_failed` circuit-broken requests are made, at which
        point the client re-logs and begins the whole cycle again.
        :param args:
        :param max_attempts:
        :param kwargs:
        :return:
        """
        breaks_in_a_row = 0
        fails = 0
        sleep_time = self.sleep_on_page

        while True:
            try:
                with self.hold_requests:
                    resp = self.request(*args, **kwargs)
                return resp
            except requests.HTTPError as e:
                self.logger.error('Error %d - %s %s ',
                                  e.request.status_code, args[0], args[1])

            except json.JSONDecodeError:
                self.logger.error('Response not in JSON format: %s - %s',
                                  args[0], args[1])
            except Exception as e:
                self.logger.error('Exception occurred - ' + repr(e)[:100])

            fails += 1
            if fails >= self.requests_to_break:
                breaks_in_a_row += 1
                time.sleep(self.sleep_on_break)
                sleep_time = self.sleep_on_page
            else:
                time.sleep(sleep_time)
                sleep_time *= self.exponential_sleep_increase

            # If request is circuit-broken 5 times in a row then
            # attempt to re-log the account before trying again
            if breaks_in_a_row >= 5:
                fails = 0
                breaks_in_a_row = 0
                self.logout()
                time.sleep(60)
                self.login()

            if 0 < max_attempts < fails:
                raise requests.ConnectionError(
                    'After %d attempts failed to %s %s' % (
                        max_attempts, args[0], args[1]
                    ))

    def setup(self, username, password, session):
        """
        Setup session variables by username/password or by previous session
        :param username:
        :param password:
        :param session:
        :return:
        """

        self._assert_session_data_correct(username, password, session)
        self.password = password

        if session:
            self._cookies = session.get('cookies')
            self.username = self._cookies['ds_user']
            self.device_id = session.get('device_id')
            self.username_id = session.get('uid')
            self.uuid = session.get('uuid')
            self.token = session.get('token')
            self._session.cookies.update(self._cookies)
        else:
            self._cookies = None
            self.username = username
            h = md5((username + password).encode('utf-8')).hexdigest()
            self.device_id = generate_device_id(h)
            self.username_id = None
            self.uuid = generate_uuid(True)
            self.token = None

    def set_proxy(self, proxy):
        """
        Set proxy for all requests made with this session
        :param proxy: str: proxy - format: "user:password@ip:port" OR "ip:port"
        """
        self._session.proxies.update({
            'http': 'http://' + proxy, 'https': 'http://' + proxy
        })

    def url(self, path, *args):
        """Return url for api path formatted with args"""
        return urljoin(BASE_URL, self.paths[path].format(*args))

    @contextmanager
    def wait_limit(self, url):
        """

        :param url:
        :return:
        """
        for path, limiter in self.limits.items():
            if re.search(path, url):
                with limiter:
                    yield
                break
        else:
            yield

    @staticmethod
    def build_form_body(bodies, boundary):
        """

        :param bodies:
        :param boundary:
        :return:
        """
        body = u''
        for b in bodies:
            body += u'--{}\r\n'.format(boundary)
            body += u'Content-Disposition: {}; ' \
                    u'name="{}"'.format(b['type'], b['name'])
            _filename = b.get('filename', None)
            _headers = b.get('headers', None)
            if _filename:
                _id = generate_upload_id()
                _filename, ext = os.path.splitext(_filename)
                body += u'; filename="pending_media_{}.{}"'.format(_id, ext)
            if _headers and isinstance(_headers, list):
                for h in _headers:
                    body += u'\r\n{}'.format(h)
            body += u'\r\n\r\n{}\r\n'.format(b['data'])
        body += u'--{}--'.format(boundary)
        return body

    def form_data_for_message(self, recipients, text=None):
        """

        :param recipients:
        :param text:
        :return:
        """
        return [
            {
                'type': 'form-data', 'name': 'recipient_users',
                'data': '[%s]' % str(recipients).replace("'", '"')
            },
            {
                'type': 'form-data', 'name': 'client_context',
                'data': self.uuid
            },
            {
                'type': 'form-data', 'name': 'thread', 'data': '["0"]',
            },
            {
                'type': 'form-data', 'name': 'text', 'data': text or '',
            }
        ]

    def upload_data_photo(self, upload_id, photo_file_object):
        return {
            '_uuid': self.uuid,
            '_csrftoken': self.token,
            'upload_id': str(upload_id),
            'image_compression': '{"lib_name":"jt",'
                                 '"lib_version":"1.3.0","quality":"87"}',
            'photo': (
                'pending_media_%s.jpg' % upload_id,
                photo_file_object,
                'application/octet-stream',
                {'Content-Transfer-Encoding': 'binary'}
            )
        }

    @staticmethod
    def form_headers(boundary):
        """

        :param boundary:
        :return:
        """
        return {
            'User-Agent': USER_AGENT,  # todo maybe don't need
            'Proxy-Connection': 'keep-alive',
            'Connection': 'keep-alive',
            'Accept': '*/*',  # todo maybe don't need
            'Content-Type': 'multipart/form-data;'
                            ' boundary={}'.format(boundary),
            'Accept-Language': 'en-en'
        }

    @staticmethod
    def upload_headers(content_type, video=False):
        """

        :param content_type:
        :param video:
        :return:
        """
        return {
            'X-IG-Capabilities': '3Q4=',
            'X-IG-Connection-Type': 'WIFI',
            'Cookie2': '$Version=1',  # todo maybe don't need
            'Accept-Language': 'en-US',
            'Accept-Encoding': 'gzip, deflate',
            'Content-type': content_type,
            'Connection': 'keep-alive' if video else 'close',
            'User-Agent': USER_AGENT  # todo maybe don't need
        }

    @staticmethod
    def configure_data(width, height, upload_id, caption, video=False):
        return {
            'source_type': 3 if video else 4,
            'caption': caption or '',
            'upload_id': upload_id,
            'device': DEVICE_SETTINGS,
            'extra': {
               'source_width': width,
               'source_height': height
            }
        }

    @staticmethod
    def configure_data_photo(width, height):
        return {
            'media_folder': 'Instagram',
            'edits': {
                'crop_original_size': [width * 1.0, height * 1.0],
                'crop_center': [0.0, 0.0],
                'crop_zoom': 1.0
            },
        }

    @staticmethod
    def configure_data_video(duration):
        return {
            'poster_frame_index': 0,
            'length': 0.00,
            'audio_muted': False,
            'filter_type': 0,
            'video_result': 'deprecated',
            'clips': {
                'length': duration,
                'source_type': '3',
                'camera_position': 'back',
            }
        }

    @staticmethod
    def _assert_session_data_correct(username, password, session):
        if session:
            cookies = session.get('cookies', {})
            for k in ['ds_user', 'ds_user_id', 'csrftoken', 'sessionid',
                      'shbid', 'shbts', 'urlgen', 'rur']:
                assert k in cookies, 'session cookies mising data: %s' % k
            for k in ['device_id', 'token', 'uid', 'uuid']:
                assert k in session, 'session missing data: %s' % k
        else:
            assert username and password, 'Must provide username and password'
