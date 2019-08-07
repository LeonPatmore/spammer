# Spammer
Spammer is a performance testing tool for Python, made to make custom 
implementation as easy as possible. In reality, it is just some simple
wrappers for the python module gevent.

## Wrappers
### SpammerRequester
Spammer requester is a simple HTTP requester that uses requests
session to pool connections. However, we also implement an in memory 
DNS cache to reduce load on the OS and DNS servers.

You can create an object like the following:
```python 
SpammerRequester(connection_pool_size=300)
```
- connection_pool_size: Number of connections in the connection pool.

 
