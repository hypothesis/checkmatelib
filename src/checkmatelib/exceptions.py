"""Exceptions for the Checkmate client."""

from functools import wraps

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
            raise BadURL(err.args[0]) from err

        except REQUESTS_UPSTREAM_SERVICE as err:
            raise CheckmateServiceError(err.args[0]) from err

        except exceptions.RequestException as err:
            raise CheckmateException(err.args[0]) from err

    return deco
