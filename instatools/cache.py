"""Response caching for testing integration with instatools"""

import os
import pickle
import re
import sqlite3
from contextlib import contextmanager

import requests

import instatools.api
import instatools.instagram.feeds
import instatools.session


def clear(data_dir):
    db_path = os.path.join(data_dir, 'instagram_cache.db')
    if os.path.exists(db_path):
        os.remove(db_path)


@contextmanager
def read(data_dir):

    db_path = os.path.join(data_dir, 'instagram_cache.db')
    if not os.path.exists(data_dir) or not os.path.exists(db_path):
        raise FileNotFoundError(
            'You must record a request before reading from the cache')

    old_request = instatools.session.Session._session_class.request
    instatools.session.Session._session_class.request = \
        _handle_request(data_dir, old_request)
    instatools.api.sleep_between_pages = 0
    instatools.instagram.feeds.FeedReader._sleep_between_reads = 0
    yield
    instatools.session.Session._session_class.request = old_request


@contextmanager
def record(data_dir):

    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    cache = DataBaseCache(os.path.join(data_dir, 'instagram_cache.db'))
    old_request = requests.Session.request

    def _request(self, method, url, **kwargs):
        resp = old_request(self, method, url, **kwargs)
        cache.set(url, pickle.dumps(resp))
        return resp

    instatools.session.Session._session_class.request = _request
    instatools.api.sleep_between_pages = 0
    instatools.instagram.feeds.FeedReader._sleep_between_reads = 0
    yield
    instatools.session.Session._session_class.request = old_request


class DataBaseCache(object):

    def __init__(self, db_path, default_factories=None):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('create table if not exists cache(key, value)')
        self.conn.commit()
        self._cache = {}
        self._default_factories = default_factories or {}
        for k, v in self.cursor.execute('select * from cache').fetchall():
            self._cache[k] = v

    def __del__(self):
        self.conn.commit()
        self.conn.close()

    def get(self, key):
        result = self._cache.get(key, None)
        if result is not None:
            return result
        else:
            for k, v in self._cache.items():
                if k.startswith(key):
                    return v

            for k, factory in self._default_factories.items():
                if re.search(k, key) is not None:
                    if callable(factory):
                        return factory()
                    return factory

    def set(self, key, value):
        self.cursor.execute('insert into cache values (?, ?)', (key, value))
        self.conn.commit()
        self._cache[key] = value

    def delete(self, key):
        self.cursor.execute('delete from cache where key=?', (key,))
        self.conn.commit()
        del self._cache[key]

    def clear(self):
        self.cursor.execute('drop table cache')
        self.cursor.execute('create table cache(key, value)')
        self.conn.commit()


def _handle_request(data_dir, request_method):
    success_response = requests.Response()
    success_response.status_code = 200
    success_response._content = b'{"status":"ok"}'
    cache = DataBaseCache(
        os.path.join(data_dir, 'instagram_cache.db'),
        default_factories={
            '.*': pickle.dumps(success_response)
        })

    def _request(self, method, url, **kwargs):
        if 'i.instagram.com/api' in url:
            result = cache.get(url)
            if result is not None:
                response = pickle.loads(result)
                response.cookies.update({'csrftoken': 'token'})
                return response

        return request_method(self, method, url, **kwargs)

    return _request
