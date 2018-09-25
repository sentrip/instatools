"""
Wrappers for interactions with Instagram API
"""
from functools import wraps
from time import sleep, monotonic as time
from instatools.models import ModelFactory

# todo logging
max_seen_items = 1000000
sleep_between_pages = 0.5
_feed_dict = {}
_feed_dict.update({k: ModelFactory.comment
                   for k in ['comments']})
_feed_dict.update({k: ModelFactory.user
                   for k in ['user', 'following', 'followers', 'pending']})
_feed_dict.update({k: ModelFactory.post
                   for k in ['tag_feed', 'location_feed', 'user_feed',
                             'user_tags', 'timeline', 'liked', 'saved']})
_ranked_feeds = ['tag_feed', 'user_feed', 'location_feed',
                 'user_tags', 'popular', 'timeline']
_user_feeds = ['following', 'followers', 'pending']


def requires_login(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        # assert self.logged_in, \
        #    'Login required for this endpoint'
        return func(self, *args, **kwargs)
    return wrapped


class ApiMethod:
    def __init__(self, api):
        self.api = api

    @requires_login
    def action(self, path, *args, max_attempts=10, return_key='', extra=None,
               method='POST', headers=None, params=None, data=None):
        """

        :param path:
        :param args:
        :param max_attempts:
        :param return_key:
        :param extra:
        :param method:
        :param headers:
        :param params:
        :param data:
        :return:
        """
        data = data or {}
        if 'friendship' in self.api.session.paths[path] and args:
            data['user_id'] = args[0]
        elif 'media' in self.api.session.paths[path] and args:
            data['media_id'] = args[0]

        self.api.logger.debug('Attempting to %s %s', path, *args)
        resp = self.api.session.request_safely(
            method, self.api.session.url(path, *args),
            data=data, headers=headers,
            params=params, max_attempts=max_attempts
        )

        return self._handle_response(resp, return_key=return_key, extra=extra)

    @requires_login
    def feed(self, feed_type, *args, seen=None, raw=False):
        """

        :param feed_type:
        :param args:
        :param seen:
        :param raw:
        :return:
        """
        url = self.api.session.url(feed_type, *args)
        params, item_keys, has_more_key = self._params_for_feed(feed_type)
        pages = _Pages(self.api, url, feed_type, params,
                       item_keys, has_more_key, raw=raw)
        return pages

    @requires_login
    def form(self, path, bodies, boundary, params=None, return_key=''):
        """

        :param path:
        :param bodies:
        :param boundary:
        :param params:
        :param return_key:
        :return:
        """
        body = self.api.session.build_form_body(bodies, boundary)
        headers = self.api.session.form_headers(boundary)

        resp = self.api.session.request_safely(
            'POST', self.api.session.url(path),
            params=params, data=body, headers=headers)

        return self._handle_response(resp, return_key)

    # todo add link sharing
    # +            bodies.append({
    # +                'type' : 'form-data',
    # +                'name' : 'link_text',
    # +                'data' : text or '',
    # +            })
    # +            bodies.append({
    # +                'type' : 'form-data',
    # +                'name' : 'link_urls',
    # +                'data' : json.dumps(self.find_urls(text)),
    # +            })

    def _handle_response(self, response, return_key='', extra=None):

        status = response.pop('status', 'error')
        if status == 'ok':
            data = response
            model = getattr(ModelFactory, return_key.strip('s'),
                            ModelFactory.default)

            if return_key and return_key in response:
                data = response[return_key]

            # Try parse data
            if data:
                # Try to return instatools model(s) from data
                try:
                    if isinstance(data, list):
                        return model.parse_list(self.api, data, extra=extra)
                    else:
                        return model.parse(self.api, data, extra=extra)
                # Otherwise return un-parsed data
                except TypeError:
                    return data
            # If no data is received, acknowledge success
            else:
                return True
        else:
            self._on_failed_request(response)
            return False

    def _on_failed_request(self, response):
        # todo write on_failed_request
        msg = 'aw shit %s' % str(response)[:100]
        self.api.logger.critical(msg)
        print(msg)
        return False

    def _params_for_feed(self, feed_type):
        params = {}
        item_keys = ['items']
        has_more_key = 'more_available'

        if feed_type in _ranked_feeds:

            params.update(rank_token=self.api.session.rank_token, ranked=True)
            item_keys = ['items', 'ranked_items']

            if feed_type == 'popular':
                params.update(people_teaser_supported=1)

        elif feed_type in _user_feeds:

            item_keys = ['users']
            has_more_key = 'big_list'

        return params, item_keys, has_more_key


class _Pages:
    def __init__(self, api, url, feed_type, params,
                 item_keys, has_more_key, raw=False):
        # todo fix seen posts filtering
        self.api = api
        self._items = []
        self._item_keys = item_keys
        self._iter = None
        self._has_more_key = has_more_key
        self._last_request = 0
        self._model = _feed_dict[feed_type]
        self._params = params or {}
        self._raw = raw
        self._url = url
        self._response = {
            has_more_key: True,
            'next_max_id': '',
            'prev_max_id': ''
        }

    def __iter__(self):
        self._iter = self.iter_items()
        return self

    def __next__(self):
        if self._iter is None:
            self._iter = self.iter_items()
        return next(self._iter)

    @property
    def items(self):
        if self._raw:
            return self._items
        else:
            return self._model.parse_list(self.api, self._items)

    def prev(self):
        self._items = self._get_data('prev')
        return self

    def next(self):
        self._items = self._get_data('next')
        return self

    def iter_pages(self):
        yield self
        while self._response.get(self._has_more_key, False):
            yield self.next()

    def iter_items(self):
        for item in self.items:
            yield item

        for page in self.iter_pages():
            for item in page.items:
                yield item

    def _get_data(self, action):
        sleep(max(0., sleep_between_pages - (time() - self._last_request)))
        self._last_request = time()

        params = self._params.copy()
        params.update(max_id=self._response['%s_max_id' % action])

        self._response = self.api.session.request_safely(
            'GET', self._url, params=params, max_attempts=3)

        data = []
        if self._response:
            for k in self._item_keys:
                data.extend(self._response.get(k, []))
        else:
            self._response = {self._has_more_key: False}
        return data
