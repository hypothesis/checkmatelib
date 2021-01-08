"""A client for the Checkmate URL testing service."""

import requests
from future.utils import raise_from  # Python 2.7 compatibility

from checkmatelib._response import BlockResponse
from checkmatelib.exceptions import CheckmateServiceError, handles_request_errors

# pylint: disable=too-few-public-methods


class CheckmateClient:
    """A client for the Checkmate URL testing service."""

    MAX_URL_LENGTH = 2000

    def __init__(self, host):
        """Initialise a client for contacting the Checkmate service.

        :param host: The host including scheme, for the Checkmate service
        """
        self._host = host.rstrip("/")

    @handles_request_errors
    def check_url(self, url, allow_all=False):
        """Check a URL for reasons to block.

        :param url: URL to check
        :param allow_all: If True, bypass Checkmate's allow-list

        :raises BadURL: If the provided URL is bad
        :raises CheckmateServiceError: If there is a problem contacting the service
        :raises CheckmateException: For any other issue with the Checkmate service

        :return: None if the URL is fine or a `CheckmateResponse` if there are
           reasons to block the URL.
        """

        # Truncate extremely long URLs so we don't get 400's and fail open
        url = url[: self.MAX_URL_LENGTH]

        params = {"url": url}

        if allow_all:
            params["allow_all"] = True

        response = requests.get(self._host + "/api/check", params=params, timeout=1)

        response.raise_for_status()

        if response.status_code == 204:
            return None

        try:
            return BlockResponse(response.json())

        except ValueError as err:
            raise_from(CheckmateServiceError("Unprocessable JSON response"), err)
