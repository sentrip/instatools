import os
import pytest
from instatools import Instagram, cache
from instatools.models import ModelFactory

# If you cant modify environment variables you can set
# username and password here, but this is risky, so careful!
username = None
password = None

if not username:
    try:
        username = os.environ.get('INSTAGRAM_USERNAME')
    except KeyError:
        raise RuntimeError(
            'Please set INSTAGRAM_USERNAME environment variable or username'
            'locally to a valid Instagram username to test api access')
if not password:
    try:
        password = os.environ.get('INSTAGRAM_PASSWORD')
    except KeyError:
        raise RuntimeError(
            'Please set INSTAGRAM_PASSWORD environment variable or password '
            'locally to the password for INSTAGRAM_USERNAME to test api access'
        )

# Only record, don't un-patch session
cache.record('tests/data').__enter__()
# We're only making and using one api, no fixtures
api = Instagram(username or '_', password or '_')
user_id = 5788087233
post_id = 1568759855441997762
# Values set globally so each different path is only requested once
comment_id = None
new_image_id = None
new_video_id = None
full_name = None


@pytest.mark.first
@pytest.mark.slow
def test_login():
    api.login()
    assert api.logged_in, 'Did not login'


@pytest.mark.slow
def test_api_from_session():
    new_api = Instagram(session=api.session.session_data)
    assert api.profile.full_name == new_api.profile.full_name


class TestDataActions:

    @pytest.mark.slow
    def test_get_comments(self):
        comments = api.get_comments(post_id)
        assert comments

    @pytest.mark.slow
    def test_get_followers_for_other_user(self):
        users = api.get_followers(user_id)
        assert users

    @pytest.mark.slow
    def test_get_following_for_other_user(self):
        users = api.get_following(user_id)
        assert users

    @pytest.mark.slow
    def test_get_friendship(self):
        success = api.get_friendship(user_id)
        assert success

    @pytest.mark.slow
    def test_get_geo_media(self):
        success = api.get_geo_media(user_id)
        assert success

    @pytest.mark.slow
    def test_get_likers(self):
        success = api.get_likers(post_id)
        assert success

    @pytest.mark.slow
    def test_get_post(self):
        success = api.get_post(post_id)
        assert success

    @pytest.mark.slow
    def test_get_story(self):
        success = api.get_story(user_id)
        assert success

    @pytest.mark.slow
    def test_get_user(self):
        success = api.get_user(user_id)
        assert success

    @pytest.mark.slow
    def test_get_followers(self):
        users = api.get_followers()
        assert users
        for user in users:
            assert isinstance(user, ModelFactory.user)

    @pytest.mark.slow
    def test_get_username(self):
        data = api.get_username('sentrip_staza1')
        assert data.id == user_id, 'Search username did not return user id'


class TestFeedActions:

    @pytest.mark.slow
    def test_feed_args(self):
        count = 0
        for item in api.feeds.tag('beach'):
            assert isinstance(item, ModelFactory.post)
            if count >= 15:
                break
            count += 1

    @pytest.mark.slow
    def test_feed_no_args(self):
        count = 0
        for item in api.feeds.timeline:
            assert isinstance(item, ModelFactory.post)
            if count >= 15:
                break
            count += 1


@pytest.mark.skip
class TestHubActions:

    @pytest.mark.slow
    def test_explore(self):
        print(api.hub.explore)

    @pytest.mark.slow
    def test_inbox(self):
        print(api.hub.inbox)

    @pytest.mark.slow
    def test_share_inbox(self):
        print(api.hub.share_inbox)

    @pytest.mark.slow
    def test_recent_activity(self):
        print(api.hub.activity)

    @pytest.mark.slow
    def test_recent_following_activity(self):
        print(api.hub.following_activity)

    @pytest.mark.slow
    def test_megaphone(self):
        print(api.hub.megaphone)


class TestMediaActions:

    @pytest.mark.slow
    def test_like(self):
        success = api.like(post_id)
        assert success, 'Did not like post'

    @pytest.mark.slow
    def test_unlike(self):
        success = api.unlike(post_id)
        assert success, 'Did not unlike post'

    @pytest.mark.slow
    def test_save(self):
        success = api.save(post_id)
        assert success, 'Did not save post'

    @pytest.mark.slow
    def test_unsave(self):
        success = api.unsave(post_id)
        assert success, 'Did not unsave post'

    @pytest.mark.slow
    def test_comment(self):
        global comment_id
        comment = api.comment(post_id, 'Test comment')
        assert comment, 'Did not comment on post'
        comment_id = comment.id

    @pytest.mark.slow
    def test_remove_comment(self):
        assert comment_id
        success = api.remove_comment(post_id, comment_id)
        assert success, 'Did not remove comment from post'


class TestProfileActions:

    @pytest.mark.slow
    def test_follow_requests(self):
        rs = api.profile.follow_requests
        for user in rs:
            assert isinstance(user, ModelFactory.user)

    @pytest.mark.slow
    def test_full_name(self):
        global full_name
        full_name = api.profile.full_name
        assert full_name

    @pytest.mark.slow
    def test_edit(self):
        # name = api.profile.full_name
        # new_name = name[1:] + name[0]
        # success = api.profile.edit(full_name=new_name)
        # assert success
        pass

    @pytest.mark.slow
    def test_full_name_changed_after_edit(self):
        assert full_name
        new_name = api.profile.full_name
        # assert new_name != full_name

    @pytest.mark.slow
    def test_remove_profile_picture(self):
        pass

    @pytest.mark.slow
    def test_change_profile_picture(self):
        pass

    @pytest.mark.slow
    def test_set_private(self):
        assert api.profile.set_private()

    @pytest.mark.slow
    def test_set_public(self):
        assert api.profile.set_public()


class TestSearchActions:
    @pytest.mark.slow
    def test_facebook(self):
        results = api.search.facebook('sentrip_staza')
        assert results

    @pytest.mark.slow
    def test_location(self):
        results = api.search.locations('beach')
        assert results

    @pytest.mark.slow
    def test_tags(self):
        results = api.search.tags('beach')
        assert results

    @pytest.mark.slow
    def test_users(self):
        results = api.search.users('sentrip_staza')
        assert results


class TestUserActions:

    @pytest.mark.slow
    def test_follow(self):
        success = api.follow(user_id)
        assert success, 'Did not follow user'

    # This test is after get following to make sure the user
    # is following at least one person (the one that is followed here)
    @pytest.mark.slow
    def test_get_following(self):
        users = api.get_following()
        assert users
        for user in users:
            assert isinstance(user, ModelFactory.user)

    @pytest.mark.slow
    def test_unfollow(self):
        assert user_id
        success = api.unfollow(user_id)
        assert success, 'Did not unfollow user'

    @pytest.mark.slow
    def test_block(self):
        success = api.block(user_id)
        assert success, 'Did not block user'

    @pytest.mark.slow
    def test_unblock(self):
        success = api.unblock(user_id)
        assert success, 'Did not un-block user'

    @pytest.mark.slow
    def test_direct_message(self):
        success = api.direct_message([user_id], 'test')
        assert success

    @pytest.mark.slow
    def test_direct_share(self):
        success = api.direct_share(post_id, [user_id], msg='test')
        assert success


class TestPosting:
    @pytest.mark.slow
    def test_post_album(self, insta):
        pass

    @pytest.mark.slow
    def test_remove_album(self, insta):
        pass

    @pytest.mark.slow
    def test_post_image(self, insta):
        pass

    @pytest.mark.slow
    def test_remove_image(self, insta):
        pass

    @pytest.mark.slow
    def test_post_video(self, insta):
        pass

    @pytest.mark.slow
    def test_remove_video(self, insta):
        pass


@pytest.mark.slow
def test_logout():
    api.logout()
    assert not api.logged_in, 'Did not logout'
