"""Exceptions for the Checkmate client."""
from functools import wraps

from future.utils import raise_from  # Python 2.7 compatibility
from requests import exceptions

REQUESTS_BAD_URL = (
    exceptions.MissingSchema,
    exceptions.InvalidSchema,
    exceptions.InvalidURL,
    exceptions.URLRequired,
)

REQUESTS_UPSTREAM_SERVICE = (
    exceptions.ConnectionError,
    exceptions.Timeout,
    exceptions.TooManyRedirects,
    exceptions.SSLError,
)


class CheckmateException(Exception):
    """Any problem with a Checkmate request."""


class CheckmateServiceError(CheckmateException):
    """A problem with the Checkmate service itself."""


class BadURL(CheckmateException):
    """An invalid URL was passed for checking."""


def handles_request_errors(inner):
    """Translate requests errors into our application errors."""

    @wraps(inner)
    def deco(*args, **kwargs):
        try:
            return inner(*args, **kwargs)

        except REQUESTS_BAD_URL as err:
            raise_from(BadURL(err.args[0]), err)

        except REQUESTS_UPSTREAM_SERVICE as err:
            raise_from(CheckmateServiceError(err.args[0]), err)

        except exceptions.RequestException as err:
            raise_from(CheckmateException(err.args[0]), err)

    return deco
