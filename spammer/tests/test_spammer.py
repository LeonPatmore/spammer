# !/usr/bin/env python
# coding=utf-8

from spammer.spam_run import SpamRun
from spammer.spammer import Spammer, TaskResult, TaskState


class SimpleSpammer(Spammer):

    def task(self):
        failed = True
        if failed:
            return TaskResult(TaskState.FAILURE,
                              reason="Failed because it failed :D",
                              response_time=100)
        else:
            return TaskResult(TaskState.SUCCESS)


if __name__ == "__main__":
    spammer = SpamRun(20, 10, SimpleSpammer())
