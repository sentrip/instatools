
from datetime import datetime
from time import sleep

from ..api import ApiMethod
from ..models import ModelFactory


class Feeds:
    def __init__(self, api=None):
        self.api = api

    @property
    def liked(self):
        return FeedReader(self.api, 'liked')

    @property
    def saved(self):
        return FeedReader(self.api, 'saved')

    @property
    def popular(self):
        return FeedReader(self.api, 'popular')

    @property
    def timeline(self):
        return FeedReader(self.api, 'timeline')

    def location(self, search):
        return FeedReader(self.api, 'location_feed', search)

    def tag(self, search):
        return FeedReader(self.api, 'tag_feed', search)

    def user(self, search):
        return FeedReader(self.api, 'user_feed', search)

    def user_tags(self, search):
        return FeedReader(self.api, 'user_tags', search)


class FeedReader:

    _sleep_between_reads = 900

    def __init__(self, api, feed_type, *args, reset_after=86400):
        self.api = api
        self.args = args
        self.feed_type = feed_type
        self.reset_after = reset_after

        self.seen = set()
        self.has_new_items = False
        self.feed = ApiMethod(self.api).feed(
            self.feed_type, *self.args, seen=self.seen)

    def __iter__(self):
        while True:
            try:
                data = next(self.feed)

            except StopIteration:
                if not self.has_new_items:
                    sleep(self._sleep_between_reads)

                self.has_new_items = False
                self.reset()

            else:

                if not self._is_recent(data):
                    continue

                self.has_new_items = True
                yield data

    def reset(self):
        self.feed = ApiMethod(self.api).feed(
            self.feed_type, *self.args, seen=self.seen)

    def _is_recent(self, item):
        return _age_of(item) <= self.reset_after


def _age_of(item):
    """
    Determine age (if possible) of an item (used for resetting feeds)
    :param item:
    :return:
    """
    created = datetime.now()

    if isinstance(item, ModelFactory.post):
        created = datetime.fromtimestamp(item.taken_at)

    return (datetime.now() - created).seconds
