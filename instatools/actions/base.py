from abc import abstractmethod
from collections import deque
from contextlib import contextmanager
from functools import partial
from heapq import heappop, heappush
from time import sleep, monotonic as time
from .helpers import ensure_time, only_daylight_hours, random_intervals


class Action:
    """Continuous Action that executes in steps over time"""
    done = False

    day_begins_at = 7
    day_ends_at = 24
    random_interval = 0

    def __init__(self, only_during_daylight=False):

        if only_during_daylight:
            self._context = partial(only_daylight_hours,
                                    self.day_begins_at, self.day_ends_at,
                                    self.random_interval)
        else:
            self._context = _dummy_context

    @abstractmethod
    def step(self, api):
        raise NotImplementedError

    def begin(self, api):
        pass

    def end(self, api):
        pass

    def cancel(self):
        self.done = True

    def restart(self):
        self.done = False

    def run(self, api):
        self.begin(api)

        while not self.done:
            with self._context():
                self.step(api)

        self.end(api)


class QueuedActions(Action):
    """
    Action that can queue commands and then execute them sequentially
    at a rate of 'per_interval' commands in the time 'interval'.
    :param per_interval: number of actions to execute in one interval
    :param interval: time in seconds for interval
    """

    def __init__(self, per_interval=30, interval=3600, **kwargs):
        super(QueuedActions, self).__init__(**kwargs)
        self.interval = interval
        self.per_interval = per_interval
        self._queue = deque(maxlen=100)

    @abstractmethod
    def update(self, api):
        """

        """
        raise NotImplementedError

    def add(self, action, *args):
        """
        Add an action onto the queue to be executed later
        :param action:
        :param args:
        """
        if (action, *args) not in self._queue:
            self._queue.append((action, *args))

    def step(self, api):
        with ensure_time(self.interval):

            begin_update = time()
            self.update(api)
            time_left = self.interval - (time() - begin_update)

            for sleep_time in random_intervals(self.per_interval, time_left):
                with ensure_time(sleep_time):

                    while not self._queue:
                        sleep(1e-3)

                    action, *args = self._queue.popleft()
                    action(*args)


class CandidateActions(QueuedActions):
    def __init__(self, action, per_hour=30, min_candidates=100):
        super(CandidateActions, self).__init__(per_hour, 3600)
        self.action = action
        self.min_candidates = min_candidates
        self.candidates = []
        self.gen = None

    @abstractmethod
    def create_gen(self, api):
        raise NotImplementedError

    @abstractmethod
    def get_score(self, api, candidate):
        raise NotImplementedError

    def before_update(self, api):
        pass

    def begin(self, api):
        self.gen = self.create_gen(api)

    def update(self, api):
        self.before_update(api)

        while len(self.candidates) <= self.min_candidates:
            item = next(self.gen)
            score = self.get_score(api, item)
            if score is not None:
                heappush(self.candidates, (score, item))

        _, best_candidate = heappop(self.candidates)
        self.add(getattr(best_candidate, self.action))


@contextmanager
def _dummy_context():
    """Dummy context to replace only_daylight_hours in Action"""
    yield
