# !/usr/bin/env python
# coding=utf-8
"""
Spammer
Developer: Leon.Patmore
"""

from .spam_run import SpamRun
from .spammer import Spammer, TaskResult, TaskState

class SimpleSpammer(Spammer):

    def task(self):
        print("Task done...")
        return TaskResult(TaskState.SUCCESS)


if __name__ == "__main__":
    spammer = SpamRun(20, 10, SimpleSpammer())
