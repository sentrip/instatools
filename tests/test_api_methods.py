
from instatools.models import ModelFactory

# Note: while the tests here are similar to those in test_api_access,
# these tests are run with mocked responses, so they are fast and
# no internet or account details are required to run the tests.
# However, due to this, the data may be outdated or incorrect, so you
# should run 'test_access_api.py' once in a while to refresh the data.

USER_ID = 5788087233
POST_ID = 1568759855441997762
COMMENT_ID = 17950495723016049


class TestAccountActions:

    def test_login(self, insta_logged_out):
        user = insta_logged_out.login()
        assert insta_logged_out.logged_in, 'Did not login'
        assert isinstance(user, ModelFactory.user)
        assert user.id == insta_logged_out.username_id

    def test_logout(self, insta_logged_out):
        insta_logged_out.login()
        result = insta_logged_out.logout()
        assert not insta_logged_out.logged_in, 'Did not logout'
        assert result


class TestDataActions:

    def test_get_comments(self, insta):
        comments = insta.get_comments(POST_ID)
        for comment in comments:
            assert isinstance(comment, ModelFactory.comment)

    def test_get_followers(self, insta):
        users = insta.get_followers()
        for user in users:
            assert isinstance(user, ModelFactory.user)

    def test_get_following(self, insta):
        users = insta.get_following()
        for user in users:
            assert isinstance(user, ModelFactory.user)

    # def test_get_followers_for_other_user(self, insta):
    #     users = insta.get_followers(USER_ID)
    #     for user in users:
    #         assert isinstance(user, ModelFactory.user)
    #
    # def test_get_following_for_other_user(self, insta):
    #     users = insta.get_following(USER_ID)
    #     for user in users:
    #         assert isinstance(user, ModelFactory.user)

    def test_get_friendship(self, insta):
        data = insta.get_friendship(USER_ID)
        assert data.to == USER_ID

    def test_get_geo_media(self, insta):
        success = insta.get_geo_media(USER_ID)
        assert success  # todo make more detailed

    def test_get_likers(self, insta):
        users = insta.get_likers(POST_ID)
        assert users
        for user in users:
            assert isinstance(user, ModelFactory.user)

    def test_get_post(self, insta):
        post = insta.get_post(POST_ID)
        assert post.id == POST_ID
        assert isinstance(post, ModelFactory.post)

    def test_get_story(self, insta):
        success = insta.get_story(USER_ID)
        assert success  # todo make more detailed

    def test_get_user(self, insta):
        user = insta.get_user(USER_ID)
        assert user.id == USER_ID
        assert isinstance(user, ModelFactory.user)

    def test_get_username(self, insta):
        data = insta.get_username('sentrip_staza1')
        assert data.id == USER_ID, 'Search username did not return user id'


class TestFeedActions:

    def test_feed_args(self, insta):
        count = 0
        for item in insta.feeds.tag('beach'):
            assert isinstance(item, ModelFactory.post)
            if count >= 15:
                break
            count += 1

    def test_feed_no_args(self, insta):
        count = 0
        for item in insta.feeds.timeline:
            assert isinstance(item, ModelFactory.post)
            if count >= 15:
                break
            count += 1


class TestMediaActions:

    def test_like(self, insta):
        success = insta.like(POST_ID)
        assert success, 'Did not like post'

    def test_unlike(self, insta):
        success = insta.unlike(POST_ID)
        assert success, 'Did not unlike post'

    def test_save(self, insta):
        success = insta.save(POST_ID)
        assert success, 'Did not save post'

    def test_unsave(self, insta):
        success = insta.unsave(POST_ID)
        assert success, 'Did not unsave post'

    def test_comment(self, insta):
        success = insta.comment(POST_ID, 'Test comment')
        assert success, 'Did not comment on post'

    def test_remove_comment(self, insta):
        success = insta.remove_comment(POST_ID, COMMENT_ID)
        assert success, 'Did not remove comment from post'


class TestProfileActions:

    def test_follow_requests(self, insta):
        rs = insta.profile.follow_requests
        for user in rs:
            assert isinstance(user, ModelFactory.user)

    def test_full_name(self, insta):
        global full_name
        full_name = insta.profile.full_name
        assert full_name

    def test_edit(self, insta):
        # name = insta.profile.full_name
        # new_name = name[1:] + name[0]
        # success = insta.profile.edit(full_name=new_name)
        # assert success
        pass

    def test_remove_profile_picture(self, insta):
        pass

    def test_change_profile_picture(self, insta):
        pass

    def test_set_private(self, insta):
        assert insta.profile.set_private()

    def test_set_public(self, insta):
        assert insta.profile.set_public()


class TestSearchActions:
    def test_facebook(self, insta):
        results = insta.search.facebook('sentrip_staza')
        assert results
        for user in results:
            assert isinstance(user, ModelFactory.user)

    def test_location(self, insta):
        results = insta.search.locations('beach')
        assert results

    def test_tags(self, insta):
        results = insta.search.tags('beach')
        assert results

    def test_users(self, insta):
        results = insta.search.users('sentrip_staza')
        assert results
        for user in results:
            assert isinstance(user, ModelFactory.user)


class TestUserActions:

    def test_follow(self, insta):
        rel = insta.follow(USER_ID)
        assert rel.following, 'Did not follow user'

    def test_unfollow(self, insta):
        rel = insta.unfollow(USER_ID)
        assert not rel.following, 'Did not unfollow user'

    def test_block(self, insta):
        rel = insta.block(USER_ID)
        assert rel.blocking, 'Did not block user'

    def test_unblock(self, insta):
        rel = insta.unblock(USER_ID)
        assert not rel.blocking, 'Did not un-block user'

    def test_direct_message(self, insta):
        assert insta.direct_message([USER_ID], 'test')

    def test_direct_share(self, insta):
        assert insta.direct_share(POST_ID, [USER_ID], msg='test')


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

