from datetime import datetime
from itertools import chain, cycle
from time import monotonic as time, sleep

from ..utils import image_from_path
from .base import Action, QueuedActions, CandidateActions
from .helpers import random_intervals_generator


def all_users(api):
    """Iterator of all Instagram users"""
    seen = set()
    searched = set()
    un_searched = set()
    while True:
        if len(un_searched) > 0:
            _id = un_searched.pop()
            searched.add(_id)
        else:
            _id = None

        users = set(api.get_followers(_id) + api.get_following(_id))

        for user in users:

            if user.id not in searched:
                un_searched.add(user.id)

            if user.id not in seen:
                seen.add(user.id)
                yield user


class PeriodicLoginOut(Action):
    """
    Log in and out of my account approx. every half hour.
    This is to appear more human, as regular people close and reopen
    the Instagram app regularly, and prolonged api usage without
    re-logging can be flagged as bot/spam behaviour.
    """
    def __init__(self, n_relogs=8, period=14400, **kwargs):
        super(PeriodicLoginOut, self).__init__(**kwargs)
        self.intervals = chain.from_iterable(
            random_intervals_generator(n_relogs, period))

    def step(self, api):
        sleep(next(self.intervals))
        api.switch_user(api.username, api.password)


class PeriodicUploads(Action):
    """
    Upload media with caption periodically
    """
    def __init__(self, post_cycle, **kwargs):
        super(PeriodicUploads, self).__init__(**kwargs)
        self.index = 0
        self.post_cycle = []
        # tuples of (datetime, path_to_media, settings_dict)
        self._post_cycle = post_cycle

    def begin(self, api):
        for t, path, settings in self._post_cycle:
            self.post_cycle.append((t,) + self.configure(api, path, settings))

    def step(self, api):
        t, path, settings = self.post_cycle[self.index]
        if datetime.now() >= t:
            upload, media, settings = self.configure(api, path, settings)
            try:
                upload(media, **settings)
            except Exception as e:
                api.logger.error('Media at %s caused %s', path, repr(e))
                sleep(60)  # wait a minute before trying again
            else:
                self.index += 1

    @staticmethod
    def configure(api, path, settings):

        if settings.pop('video', False):

            upload = api.upload.video
            # For videos 2 paths can be submitted to
            # also include a thumbnail for the video
            if isinstance(path, tuple):
                path, thumbnail_path = path
                thumbnail = image_from_path(thumbnail_path)
                settings['thumbnail'] = thumbnail
        else:
            upload = api.upload.photo

        media = image_from_path(path)

        return upload, media, settings


class FollowNewUsers(CandidateActions):
    """
    Follow users that are most likely to follow me back
    that have no existing friendship status with me
    """
    def __init__(self, *args, **kwargs):
        super(FollowNewUsers, self).__init__('follow', *args, **kwargs)

    def before_update(self, api):
        api.get_followers()

    def create_gen(self, api):
        return all_users(api)

    def get_score(self, api, candidate):
        if candidate not in api.followers:
            # Users who follow many people but are not followed by many
            # people are more likely to follow back, and if they have
            # lots of uploads then the likelihood increases further
            score = candidate.n_followers / candidate.n_following
            score -= candidate.n_posts / 1000
            return score


class KeepUnderFollowLimit(QueuedActions):
    """
    When maximum following (~7500) is reached,
    unfollow users that have the most followers
    """
    def update(self, api):
        following = api.get_following()
        if len(following) >= 7450:
            by_popularity = sorted(following, key=lambda t: t.n_followers)
            self.add(by_popularity[0].unfollow)


class LikeLeastLikedMedia(CandidateActions):
    """
    Get latest media of users I'm following
    and like the posts with the fewest likes
    """
    def __init__(self, *args, **kwargs):
        super(LikeLeastLikedMedia, self).__init__('like', *args, **kwargs)

    def create_gen(self, api):
        return cycle(api.feeds.user(u.id) for u in api.get_following())

    def get_score(self, api, candidate):
        return candidate.likes


class UnfollowAfter(QueuedActions):
    """
    Unfollow users I've been following for X amount of time
    """
    def __init__(self, per_hour=30, after=604800):
        super(UnfollowAfter, self).__init__(per_hour, 3600)
        self.after = after

    def update(self, api):
        for user in api.get_following():
            if time() - user.followed_me_at > self.after:
                self.add('unfollow', user.id)


class UnfollowNotFollowing(QueuedActions):
    """
    Unfollow users that I'm following that are not following me
    """
    def __init__(self, per_hour=30):
        super(UnfollowNotFollowing, self).__init__(per_hour, 3600)

    def update(self, api):
        followers = api.get_followers()
        for user in api.get_following():
            if user not in followers:
                self.add('unfollow', user.id)
