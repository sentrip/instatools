import os
import pytest
import sys

sys.path.append(os.path.abspath('../instatools'))
import instatools.cache
import instatools.api
from instatools.actions import Action
from instatools.bot import Bot
from instatools.instagram import Instagram


def pytest_addoption(parser):
    parser.addoption("--skip-api-access", action="store_true")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--skip-api-access"):
        skip_slow = pytest.mark.skip(reason="remove --skip-api-access option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    else:
        instatools.cache.clear('tests/data')


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
    with instatools.cache.read('tests/data'):
        api = Instagram('usr', 'pwd')
        api.login()
        # patch these because they change often
        # and are used frequently in urls
        api.session.username_id = None
        api.session.token = None
        yield api


@pytest.fixture
def insta_logged_out():
    with instatools.cache.read('tests/data'):
        api = Instagram('usr', 'pwd')
        yield api


@pytest.fixture
def session():
    with instatools.cache.read('tests/data'):
        yield
