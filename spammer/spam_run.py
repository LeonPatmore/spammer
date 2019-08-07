# !/usr/bin/env python
# coding=utf-8
"""
Spammer
Developer: Leon.Patmore
"""

from gevent import monkey, Greenlet
monkey.patch_all()

import logging
import os.path
import math
import time
import json

from sys import stdout
from multiprocessing.pool import ThreadPool
from gevent.pool import Pool

from spammer import Spammer, TaskState
from spammer import TaskResult

_DEFAULT_BATCH_THREADPOOL_SIZE = 60
_LOG_DIRECTORY = "logs"


class SpamRun(object):
    """
    This object represents an instance of a spam run.
    """

    def __init__(self, rps: int,
                 runtime: int,
                 spammer: Spammer,
                 log_file: str = "output.log",
                 output_json: str = "result.json"):
        """
        :param int rps: Desired requests per second.
        :param runtime: Desired runtime.
        :param Spammer spammer: The spammer configuration.
        :param str log_file: Name of the log file, can be None.
        :param str output_json: Name of the result JSON file to be generated, can be None.
        """
        self.timestamp = str(time.time())
        self._setup_logging(log_file)
        self.output_json = output_json
        # Init values
        self.thread_pool = ThreadPool(processes=_DEFAULT_BATCH_THREADPOOL_SIZE)
        self.failures = 0
        self.passes = 0
        self.failure_reasons = dict()
        self.response_times = list()
        self.max_response_time = 0
        self.avg_response_time = 0
        self.response_time_count = 0
        self.percentile_response_time = 0

        self.rps = rps
        self.runtime = runtime
        self.total = rps * runtime
        self.spammer = spammer
        total_requests = self.total
        self.results_left = self.total
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
                self.logger.warning("Cant keep up!")
            else:
                time.sleep(tw)

        while self.results_left > 0:
            time.sleep(5)

        for teardown in spammer.teardowns:
            teardown()

        self._summarise_results()

    def log_something(self, res):
        """
        Called when a batch passes.
        """
        pass

    def _setup_logging(self, file_name: str = None):
        """
        Setup the logger for this spam run.
        :param str file_name: Name of the log file, can be None.
        """
        # Rotate log files.
        if os.path.exists(file_name):
            os.rename(file_name, "{}-{}".format(file_name, self.timestamp))
        # Setup console handler.
        logger = logging.getLogger("spammer-{}".format(self.timestamp))
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        console_handler = logging.StreamHandler(stdout)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
        # Setup file handler.
        if file_name is not None:
            file_handler = logging.FileHandler(file_name)
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)
        self.logger = logger

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
        self.logger.info("Starting batch: {}".format(batch_no))
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
        if total <= 0:
            raise ValueError("Length of number list must be positive!")
        target_request = math.ceil(1.0 - total * percent) + 1
        if target_request >= total:
            target_request = total - 1
        return nums[target_request]

    def _generate_json_file(self):
        # Rotate existing json files.
        if os.path.exists(self.output_json):
            os.rename(self.output_json, "{}-{}".format(self.output_json, self.timestamp))
        # Construct JSON.
        result_json = {
            "rps": self.rps,
            "runtime": self.runtime,
            "total": self.total,
            "passes": self.passes,
            "failures": self.failures,
            "response_times": {
                "average": self.avg_response_time,
                "percentile": self.percentile_response_time,
                "max": self.max_response_time
            }
        }
        with open(self.output_json, "w+") as output_json:
            output_json.write(json.dumps(result_json))

    def _summarise_results(self):
        """
        Summarise the current results of this spam run. Prints both to the spammer logger, as-well a creating a JSON
        file of results.
        """
        # Calculate percentile response times.
        try:
            self.percentile_response_time = self._calculate_percentile(self.response_times, 0.95,
                                                                       self.response_time_count)
        except ValueError:
            self.logger.warning("Cannot calculate percentile!")
        # Output to logger.
        self.logger.debug("Passes: {} / {}, Failures: {}".format(self.passes, self.total, self.failures))
        self.logger.debug("Average response times: {}".format(self.avg_response_time))
        self.logger.debug("Max response times: {}".format(self.max_response_time))
        self.logger.debug("95% response times: {}".format(self.percentile_response_time))
        for failure_reason in self.failure_reasons.keys():
            self.logger.debug(" [ {} ] : {}".format(self.failure_reasons[failure_reason], failure_reason))
        # Output JSON file.
        if self.output_json is not None:
            self._generate_json_file()
