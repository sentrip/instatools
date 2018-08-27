"""
Public api for Instagram
"""
from cached_property import threaded_cached_property_ttl as cached_property
from collections import OrderedDict
from ..api import ApiMethod
from ..models import ModelFactory
from ..session import _make_logger, Session
from .feeds import Feeds
from .hub import Hub
from .profile import Profile
from .search import Search
# from .upload import Upload

# todo logging


class Instagram:

    def __init__(self, username=None, password=None, session=None):
        self.session = Session(username, password, session)
        self.logger = _make_logger(self.username)
        self.logged_in = session is not None

        self.feeds = Feeds(api=self)
        self.hub = Hub(api=self)
        self.profile = Profile(api=self)
        self.search = Search(api=self)
        # self.upload = Upload(api=self)

        self.following = Users(api=self, list_type='following')
        self.followers = Users(api=self, list_type='followers')

    @property
    def username_id(self):
        """User-id of Instagram account"""
        return self.session.username_id

    @property
    def username(self):
        """Username of Instagram account"""
        return self.session.username

    @username.setter
    def username(self, name):
        """Creates new logger based on username when set"""
        self.session.switch_user(name, self.password)
        self.logger = self.session.logger = _make_logger(name)

    @property
    def password(self):
        """Password of Instagram account"""
        return self.session.password

    @password.setter
    def password(self, password):
        """Changes session password and metadata when set"""
        self.session.switch_user(self.username, password)

    # =========================================== #
    #              ACCOUNT METHODS                #
    # =========================================== #

    def login(self):
        """Login to Instagram with account credentials provided in __init__"""
        user = self.session.login()
        if user:
            self.logged_in = True
            return ModelFactory.user.parse(self, user)
        return False

    def logout(self):
        """Logout of currently logged-in account"""
        self.logged_in = not self.session.logout()
        return not self.logged_in

    def switch_user(self, username=None, password=None, session=None):
        """Switches current account username and password - requires login"""
        # Use session hold_request lock to halt all other
        # api requests until logged into new user
        with self.session.hold_requests:
            if self.logged_in:
                if not self.logout():
                    return False
            self.session.switch_user(username, password, session)
            user = self.login()
        return user

    # =========================================== #
    #               USER METHODS                  #
    # =========================================== #

    def follow(self, user_id):
        return ApiMethod(self).action('follow', user_id,
                                      return_key='friendship_status',
                                      extra={'to': user_id})

    def unfollow(self, user_id):
        return ApiMethod(self).action('unfollow', user_id,
                                      return_key='friendship_status',
                                      extra={'to': user_id})

    def approve(self, user_id):
        return ApiMethod(self).action('approve', user_id,
                                      return_key='friendship_status',
                                      extra={'to': user_id})

    def ignore(self, user_id):
        return ApiMethod(self).action('ignore', user_id,
                                      return_key='friendship_status',
                                      extra={'to': user_id})

    def block(self, user_id):
        return ApiMethod(self).action('block', user_id,
                                      return_key='friendship_status',
                                      extra={'to': user_id})

    def unblock(self, user_id):
        return ApiMethod(self).action('unblock', user_id,
                                      return_key='friendship_status',
                                      extra={'to': user_id})

    def direct_message(self, recipients, msg):
        # todo add link detection
        # todo make utf-8 compliant for emojis
        bodies = self.session.form_data_for_message(recipients, msg)
        return ApiMethod(self).form('direct_message',
                                    bodies, self.session.uuid)

    def direct_share(self, post_id, recipients, msg=None):
        bodies = [dict(type='form-data', name='media_id', data=post_id)]
        bodies.extend(self.session.form_data_for_message(recipients, msg))
        return ApiMethod(self).form('direct_share', bodies, self.session.uuid,
                                    params={'media_type': 'photo'})

    # =========================================== #
    #               MEDIA METHODS                 #
    # =========================================== #

    def like(self, post_id):
        return ApiMethod(self).action('like', post_id)

    def unlike(self, post_id):
        return ApiMethod(self).action('unlike', post_id)

    def comment(self, post_id, text):
        return ApiMethod(self).action('comment', post_id,
                                      data={'comment_text': text},
                                      return_key='comment')

    def remove_comment(self, post_id, comment_id):
        return ApiMethod(self).action('remove_comment', post_id, comment_id)

    def save(self, post_id):
        return ApiMethod(self).action('save', post_id)

    def unsave(self, post_id):
        return ApiMethod(self).action('unsave', post_id)

    def post(self, *args):
        pass

    def remove_post(self, post_id):
        return ApiMethod(self).action('remove_post', post_id)

    def remove_tag(self, post_id):
        return ApiMethod(self).action('remove_tag', post_id)

    def edit_caption(self, post_id, new_caption):
        return ApiMethod(self).action('edit_caption', post_id,
                                      data={'caption_text': new_caption})

    # =========================================== #
    #               DATA METHODS                  #
    # =========================================== #

    def get_comments(self, post_id):
        return ApiMethod(self).action('comments', post_id,
                                      return_key='comments',
                                      extra={'media_id': post_id})

    def get_followers(self, user_id=None):
        if user_id:
            return list(ApiMethod(self).feed('followers', user_id))

        return self.followers.update()

    def get_following(self, user_id=None):
        if user_id:
            return list(ApiMethod(self).feed('following', user_id))

        return self.following.update()

    def get_friendship(self, user_id):
        return ApiMethod(self).action('friendship', user_id,
                                      return_key='friendship_status',
                                      extra={'to': user_id})

    def get_geo_media(self, user_id):
        return ApiMethod(self).action('geo_media', user_id)

    def get_likers(self, post_id):
        return ApiMethod(self).action('likers', post_id, return_key='users')

    def get_post(self, post_id):
        return ApiMethod(self).action('post', post_id, return_key='items')[0]

    def get_story(self, user_id):
        return ApiMethod(self).action('story', user_id)

    def get_user(self, user_id):
        return ApiMethod(self).action('user', user_id, return_key='user')

    def get_username(self, username):
        return ApiMethod(self).action('username', username,
                                      method='GET', return_key='user')


class Users:
    """Class representing new and removed users"""
    def __init__(self, api=None, list_type=None):
        self.all = OrderedDict()
        self.new = {}
        self.removed = {}
        self.type = list_type
        self.api = api

    def __contains__(self, item):
        return hasattr(item, 'id') and self.all.get(item.id, False)

    def __iter__(self):
        return iter(self.all.values())

    def __repr__(self):
        return "Users(total=%d, new=%d, removed=%d)" % tuple(
            map(len, [self.all, self.new, self.removed])
        )

    @cached_property(60)
    def current(self):
        return {user.id: user for user in
                ApiMethod(self.api).feed(self.type, self.api.username_id)}

    def update(self):
        users = self.current
        previous_users = set(self.all.keys())
        new_users = set(users.keys())
        new = [users[i] for i in new_users.difference(previous_users)]
        removed = [users[i] for i in previous_users.difference(new_users)]

        self.new.clear()
        self.removed.clear()
        for user in new:
            self.all[user.id] = self.new[user.id] = user
        for user in removed:
            self.removed[user.id] = user
            del self.all[user.id]

        return list(self.all.values())
