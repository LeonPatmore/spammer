# !/usr/bin/env python
# coding=utf-8
"""
Spammer
Developer: Leon.Patmore
"""

from gevent import monkey, Greenlet
monkey.patch_all()

import logging
import math
import time
from multiprocessing.pool import ThreadPool
from .spammer import Spammer, TaskState
from gevent.pool import Pool
from .spammer import TaskResult

logger = logging.getLogger(__name__)


_DEFAULT_BATCH_THREADPOOL_SIZE = 60


class SpamRun(object):
    """
    This object represents an instance of a spam run.
    """

    def __init__(self, rps: int, runtime: int, spammer: Spammer):
        """
        :param int rps: Desired requests per second.
        :param runtime: Desired runtime.
        :param Spammer spammer: The spammer configuration.
        """
        # Init values
        self.thread_pool = ThreadPool(processes=_DEFAULT_BATCH_THREADPOOL_SIZE)
        self.failures = 0
        self.passes = 0
        self.failure_reasons = dict()
        self.response_times = list()
        self.max_response_time = 0
        self.avg_response_time = 0
        self.response_time_count = 0

        self.rps = rps
        self.runtime = runtime
        self.spammer = spammer
        total_requests = rps * runtime
        self.results_left = total_requests
        self.batch_size = math.ceil(float(self.rps) / 2.0)
        batch_num = 1
        while total_requests > 0:
            ct = time.time()
            self.thread_pool.apply_async(self._pool_requests,
                                         kwds={"batch_no": batch_num},
                                         callback=self.log_something,
                                         error_callback=self.log_something)
            batch_num += 1
            total_requests -= self.batch_size
            tw = 0.5 - (time.time() - ct)
            if tw < 0.0:
                logger.warning("Cant keep up!")
            else:
                time.sleep(tw)

        while self.results_left > 0:
            time.sleep(5)

        for teardown in spammer.teardowns:
            teardown()

        self._summarise_results()

    def log_something(self, res):
        pass

    def _add_failure_reason(self, reason: str):
        """
        Counts the number of failure reasons.
        :param str reason: The given failure reason.
        """
        if reason in self.failure_reasons:
            self.failure_reasons[reason] += 1
        else:
            self.failure_reasons[reason] = 1

    def _request_finished(self, g: Greenlet):
        """
        Ran as a callback when a request has finished. We will check the result object, and add it to the global
            counters.
        :param Greenlet g: The greenlet object of this reject.
        """
        result_object = g.get()  # type: TaskResult
        result = result_object.result
        if result == TaskState.FAILURE:
            self.failures += 1
            self._add_failure_reason(result_object.reason)
        else:
            self.passes += 1
        self.results_left += -1
        # Deal with response time metrics.
        this_response_time = result_object.response_time
        if this_response_time is not None:
            self.response_times.append(this_response_time)
            self.response_time_count += 1
            if this_response_time > self.max_response_time:
                self.max_response_time = this_response_time
            self.avg_response_time = \
                (self.avg_response_time * (self.response_time_count - 1) + this_response_time) / \
                self.response_time_count

    def _pool_requests(self, batch_no: int):
        """
        Start a pool of requests (of batch size).
        :param int batch_no: This batch number.
        """
        logger.debug("Starting batch: {}".format(batch_no))
        pool = Pool(self.batch_size)
        for _ in range(self.batch_size):
            g = Greenlet(self.spammer.task)
            g.link(self._request_finished)
            pool.start(g)

    @staticmethod
    def _calculate_percentile(nums: list, percent: float, total: int = None) -> float:
        """
        :param list[float] nums: A list of numbers.
        :param float percent: The percentile to calculate.
        :param int total: If known, the total length of the nums list.
        :return: The percentile.
        :rtype: float
        """
        if total is None:
            total = len(nums)
        target_request = math.ceil(1.0 - total * percent) + 1
        if target_request >= total:
            target_request = total - 1
        return nums[target_request]

    def _summarise_results(self):
        """
        Summarise the current results of this spam run.
        """
        # Calculate percentile response times.
        logger.debug("Passes: {} / {}, failures: {}".format(self.passes, self.rps * self.runtime, self.failures))
        logger.debug("Average response times: {}".format(self.avg_response_time))
        logger.debug("Max response times: {}".format(self.max_response_time))
        logger.debug("95% response times: {}".format(self._calculate_percentile(self.response_times,
                                                                                0.95,
                                                                                self.response_time_count)))
        for failure_reason in self.failure_reasons.keys():
            logger.debug(" [ {} ] : {}".format(self.failure_reasons[failure_reason], failure_reason))
