from contextlib import contextmanager
from datetime import datetime
from random import random
from time import sleep, monotonic as time


__all__ = ['ensure_time', 'only_daylight_hours', 'random_intervals',
           'random_intervals_generator']


@contextmanager
def ensure_time(wait):
    """
    Ensure the executed code takes at least 'wait' seconds to complete
    :param wait: max number of seconds to wait after execution
    """
    start = time()
    yield
    sleep(max(0., wait - (time() - start)))


@contextmanager
def only_daylight_hours(wakeup_at=7, sleep_at=24, random_add=0):
    """
    Only execute code during the day (mimics a human sleep cycle)
    :param wakeup_at: hour to begin executing
    :param sleep_at: hour to stop executing
    :param random_add: interval for random wait after expected time
    """
    while not wakeup_at <= datetime.now().hour <= sleep_at:
        sleep(0.01)

    if random_add:
        end = time() + random() * random_add * 60
        while end - time() > 0:
            sleep(0.01)

    yield


def periodically(start_datetime, period):
    """"""


def random_intervals(n, total_time):
    """
    Generator of n random values (each approximately total_time/n)
    where the sum of the values is exactly total_time
    :param n:
    :param total_time:
    :return:
    """
    step = total_time / n
    max_variation = step / 2
    total = 0
    for i in range(n):
        var = 2 * random() * max_variation - max_variation
        sleep_time = min(step + var, total_time - total)
        total += sleep_time
        yield sleep_time


def random_intervals_generator(n, total_time):
    """
    Generator that yields new random intervals forever
    :param n:
    :param total_time:
    :return:
    """
    while True:
        yield random_intervals(n, total_time)
