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

pytestmark = pytest.mark.usefixtures('record_requests')
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


@pytest.mark.slow
class TestDataActions:

    def test_get_comments(self):
        comments = api.get_comments(post_id)
        assert comments

    def test_get_followers_for_other_user(self):
        users = api.get_followers(user_id)
        assert users

    def test_get_following_for_other_user(self):
        users = api.get_following(user_id)
        assert users

    def test_get_friendship(self):
        success = api.get_friendship(user_id)
        assert success

    def test_get_geo_media(self):
        success = api.get_geo_media(user_id)
        assert success

    def test_get_likers(self):
        success = api.get_likers(post_id)
        assert success

    def test_get_post(self):
        success = api.get_post(post_id)
        assert success

    def test_get_story(self):
        success = api.get_story(user_id)
        assert success

    def test_get_user(self):
        success = api.get_user(user_id)
        assert success

    def test_get_followers(self):
        users = api.get_followers()
        assert users
        for user in users:
            assert isinstance(user, ModelFactory.user)

    def test_get_username(self):
        data = api.get_username('sentrip_staza1')
        assert data.id == user_id, 'Search username did not return user id'


@pytest.mark.slow
class TestFeedActions:

    def test_feed_args(self):
        count = 0
        for item in api.feeds.tag('beach'):
            assert isinstance(item, ModelFactory.post)
            if count >= 15:
                break
            count += 1

    def test_feed_no_args(self):
        count = 0
        for item in api.feeds.timeline:
            assert isinstance(item, ModelFactory.post)
            if count >= 15:
                break
            count += 1


@pytest.mark.skip
@pytest.mark.slow
class TestHubActions:

    def test_explore(self):
        print(api.hub.explore)

    def test_inbox(self):
        print(api.hub.inbox)

    def test_share_inbox(self):
        print(api.hub.share_inbox)

    def test_recent_activity(self):
        print(api.hub.activity)

    def test_recent_following_activity(self):
        print(api.hub.following_activity)

    def test_megaphone(self):
        print(api.hub.megaphone)


@pytest.mark.slow
class TestMediaActions:

    def test_like(self):
        success = api.like(post_id)
        assert success, 'Did not like post'

    def test_unlike(self):
        success = api.unlike(post_id)
        assert success, 'Did not unlike post'

    def test_save(self):
        success = api.save(post_id)
        assert success, 'Did not save post'

    def test_unsave(self):
        success = api.unsave(post_id)
        assert success, 'Did not unsave post'

    def test_comment(self):
        global comment_id
        comment = api.comment(post_id, 'Test comment')
        assert comment, 'Did not comment on post'
        comment_id = comment.id

    def test_remove_comment(self):
        assert comment_id
        success = api.remove_comment(post_id, comment_id)
        assert success, 'Did not remove comment from post'


@pytest.mark.slow
class TestProfileActions:

    def test_follow_requests(self):
        rs = api.profile.follow_requests
        for user in rs:
            assert isinstance(user, ModelFactory.user)

    def test_full_name(self):
        global full_name
        full_name = api.profile.full_name
        assert full_name

    def test_edit(self):
        # name = api.profile.full_name
        # new_name = name[1:] + name[0]
        # success = api.profile.edit(full_name=new_name)
        # assert success
        pass

    def test_full_name_changed_after_edit(self):
        assert full_name
        new_name = api.profile.full_name
        # assert new_name != full_name

    def test_remove_profile_picture(self):
        pass

    def test_change_profile_picture(self):
        pass

    def test_set_private(self):
        assert api.profile.set_private()

    def test_set_public(self):
        assert api.profile.set_public()


@pytest.mark.slow
class TestSearchActions:
    def test_facebook(self):
        results = api.search.facebook('sentrip_staza')
        assert results

    def test_location(self):
        results = api.search.locations('beach')
        assert results

    def test_tags(self):
        results = api.search.tags('beach')
        assert results

    def test_users(self):
        results = api.search.users('sentrip_staza')
        assert results


@pytest.mark.slow
class TestUserActions:

    def test_follow(self):
        success = api.follow(user_id)
        assert success, 'Did not follow user'

    # This test is after get following to make sure the user
    # is following at least one person (the one that is followed here)
    def test_get_following(self):
        users = api.get_following()
        assert users
        for user in users:
            assert isinstance(user, ModelFactory.user)

    def test_unfollow(self):
        assert user_id
        success = api.unfollow(user_id)
        assert success, 'Did not unfollow user'

    def test_block(self):
        success = api.block(user_id)
        assert success, 'Did not block user'

    def test_unblock(self):
        success = api.unblock(user_id)
        assert success, 'Did not un-block user'

    def test_direct_message(self):
        success = api.direct_message([user_id], 'test')
        assert success

    def test_direct_share(self):
        success = api.direct_share(post_id, [user_id], msg='test')
        assert success


@pytest.mark.slow
class TestPosting:
    def test_post_album(self, insta):
        pass

    def test_remove_album(self, insta):
        pass

    def test_post_image(self, insta):
        pass

    def test_remove_image(self, insta):
        pass

    def test_post_video(self, insta):
        pass

    def test_remove_video(self, insta):
        pass


@pytest.mark.slow
def test_logout():
    api.logout()
    assert not api.logged_in, 'Did not logout'
