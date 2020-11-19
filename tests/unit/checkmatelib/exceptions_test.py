import pytest
from requests import RequestException

from checkmatelib.exceptions import (
    REQUESTS_BAD_URL,
    REQUESTS_UPSTREAM_SERVICE,
    BadURL,
    CheckmateException,
    CheckmateServiceError,
    handles_request_errors,
)


class TestHandlesRequestErrors:
    @pytest.mark.parametrize("exception", REQUESTS_BAD_URL)
    def test_it_catches_bad_url(self, raiser, exception):
        with pytest.raises(BadURL):
            raiser(exception("Oh dear"))

    @pytest.mark.parametrize("exception", REQUESTS_UPSTREAM_SERVICE)
    def test_it_catches_service_failures(self, raiser, exception):
        with pytest.raises(CheckmateServiceError):
            raiser(exception("Oh dear"))

    def test_it_catches_all_other_requests_errors(self, raiser):
        with pytest.raises(CheckmateException):
            raiser(RequestException("Oh dear"))

    @pytest.fixture
    def raiser(self):
        @handles_request_errors
        def raiser(error):
            raise error

        return raiser
