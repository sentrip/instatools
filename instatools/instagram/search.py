
from ..api import ApiMethod


class Search:
    def __init__(self, api=None):
        self.api = api

    def facebook(self, users):
        query = users
        return self._search(
            'facebook_search',
            {
                'query': query,
                'context': 'blended'
            },
            'users'
        )

    def locations(self, location):
        return self._search(
            'location_search',
            {
                'query': location
            },
            'items'
        )

    def tags(self, tag):
        return self._search(
            'tag_search',
            {
                'q': tag,
                'is_typeahead': True
            }, 'results'
        )

    def users(self, username):
        return self._search(
            'user_search',
            {
                'query': username,
                'is_typeahead': True,
                'ig_sig_key_version': 4
            },
            'users'
        )

    def _search(self, path, params, return_key=None):
        params.update(rank_token=self.api.session.rank_token)
        return ApiMethod(self.api).action(path,
                                          params=params,
                                          return_key=return_key)
