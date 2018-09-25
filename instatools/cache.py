"""Response caching for testing integration with instatools"""

import glob
import os
import requests
from contextlib import contextmanager

import instatools.api
import instatools.instagram.feeds
import instatools.session


def _handle_request(data_dir, _req):

    def _request(self, method, url, **kwargs):
        if 'i.instagram.com/api' in url:
            resp = requests.Response()
            resp.url = url
            try:
                with open(os.path.join(data_dir, 'urls.txt')) as rf:
                    for i, ln in enumerate(rf):
                        if ln.startswith(resp.url):
                            with open(os.path.join(data_dir,
                                                   '%d.txt' % i)) as f:
                                result = f.read()
                            break
                    else:
                        result = '{"status": "ok"}'
            except Exception as e:
                resp.status_code = 404
                resp._content = b'{"status": "error"}'
            else:
                resp.status_code = 200
                resp._content = result.encode('utf-8')
            resp.cookies.update({'csrftoken': 'token'})
            return resp
        else:
            return _req(self, method, url, **kwargs)
    return _request


def clear(data_dir):

    url_path = os.path.join(data_dir, 'urls.txt')
    if os.path.exists(url_path):
        os.remove(url_path)
    for fil in glob.glob(os.path.join(data_dir, '*.txt')):
        os.remove(fil)


@contextmanager
def read(data_dir):

    url_path = os.path.join(data_dir, 'urls.txt')
    if not os.path.exists(data_dir) or not os.path.exists(url_path):
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

    old_request = requests.Session.request

    def _request(self, method, url, **kwargs):
        resp = old_request(self, method, url, **kwargs)
        if resp.text != '{"status": "ok"}':
            with open(os.path.join(data_dir, 'urls.txt'), 'a') as f:
                f.write(resp.url + '\n')
            fname = os.path.join(data_dir, '%d.txt') % (
                len(os.listdir(data_dir)) - 1)
            with open(fname, 'w') as f:
                f.write(resp.text)

        return resp

    instatools.session.Session._session_class.request = _request
    instatools.api.sleep_between_pages = 0
    instatools.instagram.feeds.FeedReader._sleep_between_reads = 0
    yield
    instatools.session.Session._session_class.request = old_request
