from threading import Thread, Lock, Event
from time import sleep

from .instagram import Instagram


class Bot:
    def __init__(self, username=None, password=None, session=None,
                 actions=()):
        self.api = Instagram(username, password, session)

        self._actions = {}
        self._used_ids = set()
        self._workers = {}
        self._kill_event = Event()
        self._mutex = Lock()

        for action in actions:
            self.add_action(action)

    @property
    def running(self):
        """
        Is the bot running and available to submit Actions
        :return: boolean: running
        """
        return not self._kill_event.is_set()

    def add_action(self, action):
        """
        Add an Action to the queue of actions. This does not start
        the action, it only creates a Thread ready to execute it.
        :param action: function or instance of Action
        :return:
        """
        with self._mutex:
            _id = max(self._used_ids) if self._used_ids else 0
            while _id in self._used_ids:
                _id += 1
            self._actions[_id] = action
            self._used_ids.add(_id)
            self._workers[_id] = Thread(target=action.run, args=(self.api,))

        return _id

    def remove_action(self, _id):
        """
        Remove an Action from the queue of actions.
        Once this is done the Bot cannot restart the action.
        :param _id:
        """
        assert _id in self._workers, 'Unknown action id'
        assert not self._workers[_id].is_alive(), \
            'Cannot remove a action that is currently running'
        with self._mutex:
            self._used_ids.remove(_id)
            del self._workers[_id], self._actions[_id]

    def start_action(self, _id):
        """
        Run an action
        :param _id:
        """
        worker = self._workers[_id]
        assert not worker.is_alive(), \
            'Cannot start a action that is already running'
        with self._mutex:
            if worker._started.is_set():
                self._actions[_id].restart()
                self._workers[_id] = Thread(
                    target=self._actions[_id].run, args=(self.api,))

        self._workers[_id].start()

    def stop_action(self, _id, block=True):
        """
        Stop a currently running action
        :param _id:
        :param block:
        """
        self._actions[_id].cancel()
        if block:
            self._workers[_id].join()

    def start(self):
        """
        Start all the actions currently in the queue
        """
        for _id in self._workers:
            self.start_action(_id)

    def stop(self):
        """
        Set stop flag to kill all running actions
        """
        self._kill_event.set()

    def wait(self, _id):
        """
        Wait for an Action to finish executing
        :param _id:
        :return:
        """
        while not self._actions[_id].done:
            sleep(1e-3)

    def close(self, block=True):
        """
        Stop and remove all currently running actions
        :param block: Whether to wait for actions to be stopped
        """
        self.stop()
        for _id in self._workers.copy():
            self.stop_action(_id, block=block)
            self.remove_action(_id)

    def run(self, threaded=False):
        """
        Run the Bot, executing all actions, even ones added in the future
        :param threaded: Whether to block or defer the main loop to a Thread
        """
        if threaded:
            Thread(target=self._run).start()
        else:
            self._run()

    def _run(self):
        self.start()
        try:
            while self.running:
                sleep(1e-2)
        finally:
            self.close()
