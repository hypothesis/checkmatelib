import pytest
from requests.exceptions import HTTPError, InvalidURL, Timeout

from checkmatelib.client import CheckmateClient
from checkmatelib.exceptions import BadURL, CheckmateException, CheckmateServiceError


class TestCheckmateClient:
    def test_it_with_an_unblocked_response(self, client, response):
        response.status_code = 204

        hits = client.check_url("http://good.example.com")

        assert not hits
        response.json.assert_not_called()

    def test_it_with_a_blocked_response(
        self, client, requests, response, BlockResponse
    ):
        hits = client.check_url("http://bad.example.com")

        requests.get.assert_called_once_with(
            "http://checkmate.example.com/api/check",
            params={"url": "http://bad.example.com/"},
            timeout=1,
            auth=("API_KEY", ""),
        )

        assert hits == BlockResponse.return_value
        BlockResponse.assert_called_once_with(response.json.return_value)

    def test_allow_all(self, client, requests):
        client.check_url("http://bad.example.com", allow_all=True)

        assert requests.get.call_args[1]["params"].get("allow_all")

    def test_blocked_for(self, client, requests):
        client.check_url("http://bad.example.com", blocked_for="lms")

        assert requests.get.call_args[1]["params"].get("blocked_for")

    def test_ignore_reasons(self, client, requests):
        reasons = "reason1,reason2"
        client.check_url("http://bad.example.com", ignore_reasons=reasons)

        assert requests.get.call_args[1]["params"]["ignore_reasons"] == reasons

    @pytest.mark.parametrize(
        "exception,expected",
        (
            (Timeout, CheckmateServiceError),
            (InvalidURL, BadURL),
            (HTTPError, CheckmateException),
        ),
    )
    def test_failed_connection(self, client, requests, exception, expected):
        requests.get.side_effect = exception("Something bad")
        with pytest.raises(expected):
            client.check_url("http://bad.example.com")

    def test_failed_response(self, client, response):
        response.raise_for_status.side_effect = HTTPError("Something bad")

        with pytest.raises(CheckmateException):
            client.check_url("http://bad.example.com")

    def test_it_with_a_bad_json_payload(self, client, response):
        response.json.side_effect = ValueError

        with pytest.raises(CheckmateException):
            client.check_url("http://bad.example.com")

    @pytest.mark.parametrize("prefix", ("http://", ""))
    @pytest.mark.parametrize("path", ("/path", ""))
    @pytest.mark.parametrize(
        "bad_url",
        (
            # Local things
            "127.0.0.1",
            "localhost",
            # Not public domains
            "my_private_name",
            "index.php",
            # Malformed URL (confused for IPV6)
            "example.com]",
        ),
    )
    def test_it_with_bad_domains(self, client, prefix, bad_url, path):
        with pytest.raises(BadURL):
            client.check_url(prefix + bad_url + path)

    def test_it_truncates_very_long_urls(self, client, requests):
        very_long_url = "http://example.com/" + "a" * 10000

        client.check_url(very_long_url)

        _, kwargs = requests.get.call_args

        called_url = kwargs["params"]["url"]
        assert len(called_url) == client.MAX_URL_LENGTH
        assert called_url == very_long_url[: client.MAX_URL_LENGTH]

    @pytest.fixture
    def client(self):
        return CheckmateClient(host="http://checkmate.example.com/", api_key="API_KEY")

    @pytest.fixture
    def response(self, requests):
        response = requests.get.return_value
        response.status_code = 200

        return response


@pytest.fixture(autouse=True)
def BlockResponse(patch):
    return patch("checkmatelib.client.BlockResponse")


@pytest.fixture(autouse=True)
def requests(patch):
    requests = patch("checkmatelib.client.requests")

    return requests
