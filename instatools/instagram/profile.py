from cached_property import threaded_cached_property
from ..api import ApiMethod


class Profile:
    def __init__(self, api=None):
        self.api = api

    @property
    def biography(self):
        return self._user.bio

    @property
    def external_url(self):
        return self._user.external_url

    @property
    def full_name(self):
        return self._user.full_name

    @property
    def follow_requests(self):
        return ApiMethod(self.api).feed('pending')

    def threads(self, thread, cursor=None):
        # todo fix for usability
        params = {'cursor': cursor} if cursor else {}
        return ApiMethod(self.api).action('direct_threads', thread,
                                          params=params)

    def change_password(self, new_password):
        success = ApiMethod(self.api).action('change_password', data={
            'old_password': self.api.password,
            'new_password1': new_password,
            'new_password2': new_password
        })
        if success:
            self.api.switch_user(self.api.username, new_password)
        return success

    def change_profile_picture(self):
        pass

    def edit(self, phone, email, *, full_name=None, username=None,
             url=None, biography=None, gender=None):

        data = {
            'phone_number': phone,
            'email': email,
            'full_name': full_name or self.full_name,
            'username': username or self.api.username,
            'external_url': url or self.external_url,
            'biography': biography or self.biography,
        }
        if gender:
            data['gender'] = gender

        return self._edit('edit_profile', data=data)

    def remove_profile_picture(self):
        return self._edit('remove_profile_picture')

    def set_public(self):
        return self._edit('set_public')

    def set_private(self):
        return self._edit('set_private')

    @threaded_cached_property
    def _user(self):
        return ApiMethod(self.api).action('profile',
                                          params={'edit': True},
                                          return_key='user')

    def _edit(self, *args, **kwargs):
        success = ApiMethod(self.api).action(*args, **kwargs)
        if success and '_user' in self.__dict__:
            # Invalidate cached profile
            del self.__dict__['_user']
        return success
