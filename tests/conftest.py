from unittest.mock import MagicMock

import glob
import os
import pytest
import sys
import requests

sys.path.append(os.path.abspath('../instatools'))
import instatools.instagram.api
from instatools.actions import Action
from instatools.bot import Bot
from instatools.instagram import Instagram
from instatools.instagram.feeds import FeedReader
from instatools.session import Session


def pytest_addoption(parser):
    parser.addoption("--skip-api-access", action="store_true")


def pytest_collection_modifyitems(config, items):

    if not os.path.exists('tests/data'):
        os.mkdir('tests/data')

    if config.getoption("--skip-api-access"):
        skip_slow = pytest.mark.skip(reason="remove --skip-api-access option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    else:
        if not os.path.exists('tests/data/urls.txt'):
            with open('tests/data/urls.txt', 'w'):
                pass
        for fil in glob.glob('tests/data/*.txt'):
            os.remove(fil)
        with open('tests/data/urls.txt', 'w'):
            pass


def handle_request(*args, **kwargs):
    resp = requests.Response()
    method, resp.url = args
    try:
        try:
            with open('tests/data/urls.txt') as rf:
                for i, ln in enumerate(rf):
                    if ln.startswith(resp.url):
                        with open('tests/data/%d.txt' % i) as f:
                            result = f.read()
                        break
                else:
                    result = '{"status": "ok"}'
        except FileNotFoundError:
            result = '{"status": "ok"}'

    except:
        resp.status_code = 404
        resp._content = b'{"status": "error"}'
    else:
        resp.status_code = 200
        resp._content = result.encode('utf-8')
    resp.cookies.update({'csrftoken': 'token'})
    return resp


def _patched_session():
    sess = Session('usr', 'pwd')
    sess._session.request = MagicMock()
    sess._session.request.side_effect = handle_request
    instatools.instagram.api.sleep_between_pages = 0
    FeedReader._sleep_between_reads = 0
    return sess


class DummyAction(Action):
    def __init__(self):
        super(DummyAction, self).__init__()
        self.begun = self.finished = False
        self.count = 0

    def begin(self, api):
        self.begun = True

    def end(self, api):
        self.finished = True

    def step(self, api):
        self.count += 1
        if self.count >= 5:
            self.done = True


@pytest.fixture
def action():
    return DummyAction()


@pytest.fixture
def bot():
    return Bot('username', 'password')


@pytest.fixture
def insta():
    api = Instagram('usr', 'pwd')
    api.session = _patched_session()
    api.login()
    # patch these because they change often
    # and are used frequently in urls
    api.session.username_id = None
    api.session.token = None
    return api


@pytest.fixture
def insta_logged_out():
    api = Instagram('usr', 'pwd')
    api.session = _patched_session()
    return api


@pytest.fixture
def session():
    return _patched_session()
