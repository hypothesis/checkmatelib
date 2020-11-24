"""A client for the Checkmate URL testing service."""

import requests
from future.utils import raise_from  # Python 2.7 compatibility

try:
    from urllib.parse import urlparse
except ImportError:
    # Python 2.7 compatibility
    from urlparse import urlparse

from checkmatelib._response import BlockResponse
from checkmatelib.exceptions import (
    BadURL,
    CheckmateServiceError,
    handles_request_errors,
)

# pylint: disable=too-few-public-methods


class CheckmateClient:
    """A client for the Checkmate URL testing service."""

    def __init__(self, host):
        """Initialise a client for contacting the Checkmate service.

        :param host: The host including scheme, for the Checkmate service
        """
        self._host = host.rstrip("/")

    @handles_request_errors
    def check_url(self, url):
        """Check a URL for reasons to block.

        :param url: URL to check
        :raises BadURL: If the provided URL is bad
        :raises CheckmateServiceError: If there is a problem contacting the service
        :raises CheckmateException: For any other issue with the Checkmate service
        :return: None if the URL is fine or a `CheckmateResponse` if there are
           reasons to block the URL.
        """

        self._validate_url(url)

        response = requests.get(
            self._host + "/api/check", params={"url": url}, timeout=1
        )

        response.raise_for_status()

        if response.status_code == 204:
            return None

        try:
            return BlockResponse(response.json())

        except ValueError as err:
            raise_from(CheckmateServiceError("Unprocessable JSON response"), err)

    @classmethod
    def _validate_url(cls, url):
        """Check a URL for errors before we send it off to checkmate.

        This is intended to catch mistakes that will inevitably result in a
        bad request response.

        :param url: URL to check
        :raises BadURL: If the URL has a problem that would make the call fail
        """
        parts = urlparse(url)

        # URL parse gets confused with bare domains like: 'google.com/path'
        # and thinks the whole thing is a path, so we should try again with a
        # fake scheme to determine if there really is a domain
        if not parts.scheme and not parts.netloc:
            parts = urlparse("http://" + url.lstrip("/"))

        if not parts.netloc:
            raise BadURL("The provided url: '{}' has no domain".format(url))
