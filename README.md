# Spammer

Spammer is a performance testing tool for Python, made to make custom 
implementation as easy as possible. In reality, it is just some simple
wrappers for the python module gevent. Ideally, you would use this tool to 
send a lot of HTTP requests.

## Classes

### SpammerRequester

Spammer requester is a simple HTTP requester that uses the requests
session to pool connections. However, we also implement an in memory 
(long-lived) DNS cache to increase performance. 

You can create an requester like this:

```python 
SpammerRequester(connection_pool_size=300)
```
- connection_pool_size: Number of connections in the connection pool.

### Spammer

The Spammer object is a description of a task. You must implement
this class yourself and define the `task` function. The task function
should return an instance of `TaskResult`.

In the following example, we have a Spammer where the task always fails.
 ```python
class SimpleSpammer(Spammer):

    def task(self):
        failed = True
        if failed:
            return TaskResult(TaskState.FAILURE, 
                              reason="Failed because it failed :D", 
                              response_time=100)
        else:
            return TaskResult(TaskState.SUCCESS)
``` 

### TaskResult

This object represents the result of a task. It takes 3 arguments:

- TaskState: Did the task fail or succeed.
- [Optional] reason: Reason for task failure, will be used in logs.
- [Optional] response_time: If you are sending a HTTP request in the task, you can
provider the response time here. This will be used to calculate overall metrics in
the summary.

### SpamRun

This object is an instance of a performance test.

```python
spammer = SpamRun(rps=20, 
                  runtime=10, 
                  spammer=SimpleSpammer(), 
                  log_file="output.log",
                  output_json="result.json")
```

- rps: The requests per second (number of tests per second).
- runtime: The runtime in seconds.
- spammer: The Spammer describing the task you want to spam.
- log_file: The output log file. Has a default value.
- [Optional] output_json. The output json file. By default we will generate one.
To stop generation, set this equal to `None`.

This object will automatically start the performance test.

## Logging

We log to both std out and a log file.
