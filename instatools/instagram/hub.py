
from ..api import ApiMethod


class Hub:
    def __init__(self, api=None):
        self.api = api

    @property
    def explore(self):
        return self._get('explore')

    @property
    def inbox(self):
        return self._get('inbox')

    @property
    def share_inbox(self):
        return self._get('share_inbox')

    @property
    def megaphone(self):
        return self._get('megaphone')

    @property
    def activity(self):
        return self._get('recent_activity')

    @property
    def following_activity(self):
        return self._get('recent_following_activity')

    def _get(self, path):
        return ApiMethod(self.api).action(path, method='GET')
