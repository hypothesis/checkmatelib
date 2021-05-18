"""A client for the Checkmate URL testing service."""

import requests

from checkmatelib._response import BlockResponse
from checkmatelib.exceptions import CheckmateServiceError, handles_request_errors

# pylint: disable=too-few-public-methods


class CheckmateClient:
    """A client for the Checkmate URL testing service."""

    MAX_URL_LENGTH = 2000

    def __init__(self, host, api_key):
        """Initialise a client for contacting the Checkmate service.

        CHECKMATE_API_KEY must be present to configure authentication

        :param host: The host including scheme, for the Checkmate service
        :param api_key: API key for Checkmate
        """
        self._host = host.rstrip("/")

        self._api_key = api_key

    @handles_request_errors
    def check_url(  # pylint: disable=inconsistent-return-statements
        self, url, allow_all=False, blocked_for=None, ignore_reasons=None
    ):
        """Check a URL for reasons to block.

        :param url: URL to check
        :param allow_all: If True, bypass Checkmate's allow-list
        :param blocked_for: Sets a context for the blocked pages layout/content
        :param ignore_reasons: Ignore this class of detections. Comma separated reasons.

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

        if blocked_for:
            params["blocked_for"] = blocked_for

        if ignore_reasons:
            params["ignore_reasons"] = ignore_reasons

        response = requests.get(
            self._host + "/api/check",
            params=params,
            timeout=1,
            auth=(self._api_key, "") if self._api_key else None,
        )

        response.raise_for_status()

        if response.status_code == 204:
            return None

        try:
            return BlockResponse(response.json())

        except ValueError as err:
            raise CheckmateServiceError("Unprocessable JSON response") from err
