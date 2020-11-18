"""A client for the Checkmate URL testing service."""

import requests
from future.utils import raise_from  # Python 2.7 compatibility
from requests.exceptions import ConnectionError as ConnectionError_
from requests.exceptions import HTTPError, Timeout

from checkmatelib.exceptions import CheckmateException
from checkmatelib._response import BlockResponse


# pylint: disable=too-few-public-methods

class CheckmateClient:
    """A client for the Checkmate URL testing service."""

    def __init__(self, host):
        """Initialise a client for contacting the Checkmate service.

        :param host: The host including scheme, for the Checkmate service
        """
        self._host = host.rstrip("/")

    def check_url(self, url):
        """Check a URL for reasons to block.

        :param url: URL to check
        :raises CheckmateException: With any issue with the Checkmate service
        :return: None if the URL is fine or a `CheckmateResponse` if there are
           reasons to block the URL.
        """
        try:
            response = requests.get(
                self._host + "/api/check", params={"url": url}, timeout=1
            )
        except (ConnectionError_, Timeout) as err:
            raise_from(CheckmateException("Cannot connect to service"), err)

        try:
            response.raise_for_status()
        except HTTPError as err:
            raise_from(CheckmateException("Unexpected response from service"), err)

        if response.status_code == 204:
            return None

        try:
            return BlockResponse(response.json())

        except ValueError as err:
            raise_from(CheckmateException("Unprocessable JSON response"), err)
