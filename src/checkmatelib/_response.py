"""Objects for return values from Checkmate."""

import json

import importlib_resources
from jsonschema import Draft7Validator

from checkmatelib.exceptions import CheckmateException


class BlockResponse:
    """A response from the Checkmate service with reasons to block."""

    VALIDATOR = Draft7Validator(
        json.loads(
            importlib_resources.read_binary(
                "checkmatelib.resource", "response_schema.json"
            )
        )
    )

    def __init__(self, payload):
        """Initialise a response object from the given response from Checkmate.

        :raises CheckmateException: If the payload is malformed
        :param payload: Decoded JSON response from the Checkmate service.
        """
        for error in self.VALIDATOR.iter_errors(payload):
            raise CheckmateException("Unparseable response: {}".format(error))

        self._payload = payload

    @property
    def presentation_url(self):
        """Get a URL to display this error in HTML."""
        return self._payload["links"]["html"]

    @property
    def reason_codes(self):
        """Get the list of reason codes."""
        return [reason["id"] for reason in self._payload["data"]]

    def __repr__(self):
        return "BlockResponse({})".format(repr(self._payload))
