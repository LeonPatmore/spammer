# !/usr/bin/env python
# coding=utf-8

from gevent import monkey
monkey.patch_all()

from enum import Enum


class TaskState(Enum):
    """
    The state of a Spammer task.
    """
    SUCCESS = 1
    FAILURE = 0


class TaskResult(object):
    """
    Represents the result of a Spammer task.
    """

    def __init__(self, result: TaskState, reason: str = None, response_time: int = None):
        """
        :param TaskState result: The result of the task (see TaskState class).
        :param str reason: The reason for the result, typically used with failure to express failure reason.
        :param int response_time: The response time.
        """
        self.result = result
        self.reason = reason
        self.response_time = response_time


class Spammer(object):
    """
    This object represents a Spammer configuration.
    """

    def __init__(self):
        self.teardowns = list()

    def task(self) -> TaskResult:
        """
        Spammer task to be implemented as the user requires.
        :return: Returns a task state (not an exception).
        :rtype:
        """
        raise NotImplementedError("Spammer task has not been implemented!")

    def add_teardown(self, callback: callable):
        """
        Add a teardown function to run after the Spammer has finished a run.
        :param callable callback: A callable with no arguments.
        """
        self.teardowns.append(callback)
