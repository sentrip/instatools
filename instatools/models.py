from cached_property import threaded_cached_property_ttl as cached_property
from time import time as timestamp


class _Downloader:
    pass


downloader = _Downloader()


class Model(object):
    def __init__(self, api, json):
        self._api = api
        self._json = json

    def __hash__(self):
        return getattr(self, 'id', -1)

    def __getstate__(self):
        # pickle
        pickle = dict(self.__dict__)
        try:
            del pickle['_api']  # do not pickle the API reference
        except KeyError:
            pass
        return pickle

    def __repr__(self):
        return '{:s}(id={:s})'.format(self.__class__.__name__,
                                      str(getattr(self, 'id', -1)))

    @classmethod
    def parse(cls, api, json, extra=None):
        model = cls(api, json)

        for k, v in json.items():
            setattr(model, k, v)

        if extra:
            for k, v in extra.items():
                setattr(model, k, v)

        return model

    @classmethod
    def parse_list(cls, api, json_list, extra=None):
        items = []
        for item in json_list:
            items.append(cls.parse(api, item, extra=extra))
        return items


class Comment(Model):
    @classmethod
    def parse(cls, api, json, extra=None):
        model = cls(api, json)

        for k, v in json.items():
            if k == 'pk':
                setattr(model, 'id', v)
            elif k == 'media_id':
                setattr(model, 'post_id', v)
            else:
                setattr(model, k, v)

        return model

    def reply(self, msg):
        pass

    def remove(self):
        return self._api.remove_comment(self.post_id, self.id)


# todo location model
class Location(Model):
    @classmethod
    def parse(cls, api, json, extra=None):
        model = cls(api, json)

        for k, v in json.items():
            if k == '':
                setattr(model, '', v)
            else:
                setattr(model, k, v)

        return model


class Post(Model):
    @classmethod
    def parse(cls, api, json, extra=None):
        model = cls(api, json)

        for k, v in json.items():

            # Media data
            if k == 'pk':
                setattr(model, 'id', v)
            elif k == 'id':
                setattr(model, 'media_id', v)
            elif k == 'like_count':
                setattr(model, 'likes', v)
            elif k == 'has_likes':
                setattr(model, 'liked_by_me', v)
            elif k == 'user':
                setattr(model, 'user', ModelFactory.user.parse(api, v))

            # Image / Thumbnails
            elif k == 'image_versions2':
                setattr(model, 'image_versions', sorted(
                    v.get('candidates', []),
                    key=lambda t: t['width'] * t['height']
                ))

            # Video
            elif k == 'original_width':
                setattr(model, 'width', v)
            elif k == 'original_height':
                setattr(model, 'height', v)
            elif k == 'video_duration':
                setattr(model, 'duration', v)

            else:
                setattr(model, k, v)

        return model

    @cached_property(60)
    def comments(self):
        return self._api.get_comments(self.id)

    @cached_property(60)
    def likers(self):
        return self._api.get_likers(self.id)

    def download(self):
        pass

    def upload(self):
        pass

    def save(self):
        return self._api.save(self.id)

    def unsave(self):
        return self._api.unsave(self.id)

    def share(self, user_ids, msg=None):
        return self._api.direct_share(self.id, user_ids, msg=msg)


class Relationship(Model):

    @classmethod
    def parse(cls, api, json, extra=None):
        model = cls(api, json)

        for k, v in json.items():
            setattr(model, k, v)

        if extra and extra.get('to', False):
            setattr(model, 'to', extra.get('to'))

        return model

    def __repr__(self):
        return 'Relationship(to=%s, from=%s)' % (
            self._api.username_id, self.to)


class User(Model):
    @classmethod
    def parse(cls, api, json, extra=None):
        model = cls(api, json)

        for k, v in json.items():
            if k == 'pk':
                setattr(model, 'id', v)
            elif k == 'biography':
                setattr(model, 'bio', v)
            elif k == 'is_private':
                setattr(model, 'private', v)
            elif k == 'follower_count':
                setattr(model, 'n_followers', v)
            elif k == 'following_count':
                setattr(model, 'n_following', v)
            elif k == 'media_count':
                setattr(model, 'n_posts', v)
            else:
                setattr(model, k, v)

        # This is so Users object can track other people's follow durations
        if getattr(model, 'id', -1) != api.username_id:
            model.followed_me_at = timestamp()

        return model

    @property
    def feed(self):
        return self._api.feeds.user(self.id)

    @cached_property(3600)
    def followers(self):
        return self._api.get_followers(self.id)

    @cached_property(3600)
    def following(self):
        return self._api.get_following(self.id)

    def follow(self):
        return self._api.follow(self.id)

    def unfollow(self):
        return self._api.unfollow(self.id)

    def approve(self):
        return self._api.approve(self.id)

    def ignore(self):
        return self._api.ignore(self.id)

    def block(self):
        return self._api.block(self.id)

    def unblock(self):
        return self._api.unblock(self.id)

    def direct_message(self, msg):
        return self._api.direct_message([self.id], msg)

    def direct_share(self, post_id, msg=None):
        return self._api.direct_share([self.id], post_id, msg=msg)

    def __repr__(self):
        return 'User(%s)' % (self.username,)


class ModelFactory:

    default = Model

    comment = Comment
    location = Location
    post = item = ranked_item = Post
    relationship = friendship_status = Relationship
    user = User
