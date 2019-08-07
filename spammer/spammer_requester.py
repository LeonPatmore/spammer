"""
Spammer
Developer: Leon.Patmore
"""

from gevent import monkey
monkey.patch_all()

import requests as requests
from gevent._socketcommon import gethostbyname
from requests import adapters
from urllib.parse import urlparse


class SpammerRequester(object):
    """
    An object representing a HTTP requester.
    """

    def __init__(self, connection_pool_size=300):
        """
        :param int connection_pool_size: The requester pool size.
        """
        self.session = requests.Session()
        adapter = adapters.HTTPAdapter(pool_connections=connection_pool_size,
                                       pool_maxsize=connection_pool_size,
                                       max_retries=1,
                                       pool_block=False)
        self.session.mount('http://', adapter)
        self.addr_ip_cache = dict()

    def _get_ip_from_host(self, host: str) -> str:
        """
        Get the IP of a given host name.
        :param str host: The host.
        :return: The IP.
        :rtype: str
        """
        if host in self.addr_ip_cache:
            return self.addr_ip_cache[host]
        else:
            self.addr_ip_cache[host] = gethostbyname(host)
            return self.addr_ip_cache[host]

    def request(self, *args, **kwargs) -> requests.Response:
        """
        Proxy a request to the requests library using the global session and ip cache.
        :return: The response from the request.
        :rtype: requests.Response
        """
        parsed_uri = urlparse(kwargs['url'])
        ip = self._get_ip_from_host(parsed_uri.hostname)
        kwargs['url'] = "{}://{}:{}{};{}?{}#{}".format(parsed_uri.scheme,
                                                       ip,
                                                       parsed_uri.port,
                                                       parsed_uri.path,
                                                       parsed_uri.params,
                                                       parsed_uri.query,
                                                       parsed_uri.fragment)
        return self.session.request(*args, **kwargs)
