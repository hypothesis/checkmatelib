"""An implementation of Google Web Risk URL canonicalization.

As defined here: https://cloud.google.com/web-risk/docs/urls-hashing#canonicalization
"""

import os.path
import re
from urllib.parse import ParseResult, unquote, urlparse

from netaddr import INET_ATON, AddrFormatError, IPAddress

from checkmatelib.exceptions import BadURL


class CanonicalURL:
    """Implementation of Google Web Risk URL canonicalization."""

    @classmethod
    def canonicalize(cls, url) -> str:
        """Convert a URL to a canonical form for comparison.

        This may "invent" a scheme as necessary.

        :param url: URL to normalise
        :return: A normalised version of the URL
        """
        return cls.canonical_join(cls.canonical_split(url))

    @classmethod
    def canonical_join(cls, parts: ParseResult) -> str:
        """Join canonical parts into a URL.

        This assumes you have called `canonical_split` to get the parts, and
        does not perform any cleaning itself. The fragment is always ignored,
        but is present to support the same interface as `urllib`

        :param parts: Parsed parts of the URL
        :return: A single URL string
        """
        clean_url = parts._replace(fragment=None).geturl()

        # Get around the fact that URL parse strips off the '?' if the query
        # string is empty
        if not parts.query and parts.query is not None:
            clean_url += "?"

        return clean_url

    @classmethod
    def canonical_split(cls, url) -> ParseResult:
        """Split a URL into canonical parts.

        Note the fragment is always `None`. It is only returned for
        compatibility with the arguments of `urllib.parse.urlunparse()`
        """
        url_parts = cls._pre_process_url(url)

        # Make a distinction between an empty query and no query at all. This
        # relies on us not having a fragment
        query = cls._partial_quote(url_parts.query)
        query = query if query else "" if url.endswith("?") else None

        return ParseResult(
            scheme=url_parts.scheme,
            # In the URL, percent-escape all characters that are <= ASCII 32,
            # >= 127, #, or %. The escapes should use uppercase hex characters
            netloc=cls._partial_quote(cls._canonicalize_host(url_parts.netloc)),
            path=cls._partial_quote(cls._canonicalize_path(url_parts.path)),
            params=url_parts.params,
            query=query,
            fragment=None,
        )

    BANNED_CHARS = re.compile("[\x09\x0d\x0a]")
    SCHEME_PREFIX = re.compile(r"^([A-z]+):/+")

    @classmethod
    def _pre_process_url(cls, url):
        # https://cloud.google.com/web-risk/docs/urls-hashing#canonicalization

        clean_url = url.strip()

        # First, remove tab (0x09), CR (0x0d), and LF (0x0a) characters from
        # the URL. Do not remove escape sequences for these characters,
        # like %0a.

        clean_url = cls.BANNED_CHARS.sub("", clean_url)

        # This is our own tweak, but if we have URLs like:
        # http:/example.com or http:///example.com Chrome will go there so
        # lets convert them to always have two slashes

        clean_url = cls.SCHEME_PREFIX.sub("\\1://", clean_url)

        # Second, if the URL ends in a fragment, remove the fragment. For
        # example, shorten http://google.com/#frag to http://google.com/.

        try:
            scheme, netloc, path, params, query, _fragment = urlparse(clean_url)
        except ValueError as err:
            raise BadURL("Can't canonicalize invalid URL") from err

        if not scheme:
            if not netloc:
                # Without a scheme urlparse often assumes the domain is the
                # path. To prevent this add a fake scheme and try again
                return cls._pre_process_url("http://" + url)

            # Looks like we have a domain, but no scheme, so make one up
            scheme = "http"

        # Third, repeatedly remove percent-escapes from the URL until it has
        # no more percent-escapes.

        return ParseResult(
            scheme=scheme,
            netloc=cls._repeated_unquote(netloc),
            path=cls._repeated_unquote(path),
            params=params,
            query=cls._repeated_unquote(query),
            fragment=None,
        )

    CONSECUTIVE_DOTS = re.compile(r"\.\.+")
    PORT = re.compile(r":\d+$")

    @classmethod
    def _canonicalize_host(cls, hostname):
        # https://cloud.google.com/web-risk/docs/urls-hashing#to_canonicalize_the_hostname

        # If the URL uses an internationalized domain name (IDN), the client
        # should convert the URL to the ASCII Punycode representation.
        try:
            # https://docs.python.org/3/library/codecs.html#module-encodings.idna
            hostname = hostname.encode("idna").decode("ascii")
        except UnicodeError:
            # Oh well
            pass

        # 1. Remove all leading and trailing dots.
        hostname = hostname.strip(".")

        # 2. Replace consecutive dots with a single dot.
        hostname = cls.CONSECUTIVE_DOTS.sub(".", hostname)

        # Not in the text, but in the test cases
        hostname = cls.PORT.sub("", hostname)

        # 3. If the hostname can be parsed as an IP address, normalize it to 4
        # dot-separated decimal values. The client should handle any legal
        # IP-address encoding, including octal, hex, and fewer than
        # four components.
        ip_address = cls._decode_ip(hostname)
        if ip_address:
            hostname = ip_address

        # 4. Lowercase the whole string.
        hostname = hostname.lower()

        return hostname

    CONSECUTIVE_SLASHES = re.compile("//+")

    @classmethod
    def _canonicalize_path(cls, path):
        # https://cloud.google.com/web-risk/docs/urls-hashing#to_canonicalize_the_path

        # 1. Resolve the sequences /../ and /./ in the path by replacing
        # /./ with /, and removing /../ along with the preceding path
        # component.
        if path:
            path = os.path.normpath(path) + ("/" if path.endswith("/") else "")

        # 2. Replace runs of consecutive slashes with a single slash character.
        path = cls.CONSECUTIVE_SLASHES.sub("/", path)

        return path or "/"

    @classmethod
    def _decode_ip(cls, hostname):
        """Try and spot hostnames that are really encoded IP addresses."""
        try:
            return str(IPAddress(hostname, flags=INET_ATON))
        except (AddrFormatError, ValueError):
            return None

    @classmethod
    def _repeated_unquote(cls, string):
        decoded = unquote(string)

        # Keep decoding until the string stops changing
        while decoded != string:
            string = decoded
            decoded = unquote(string)

        return decoded

    @classmethod
    def _partial_quote(cls, string):
        parts = []
        for char in string:
            char_code = ord(char)

            # In the URL, percent-escape all characters that are <= ASCII 32,
            # >= 127, #, or %. The escapes should use uppercase hex characters.
            if char_code <= 32 or char_code >= 127 or char in "#%":
                parts.append(f"%{char_code:02X}")
            else:
                parts.append(char)

        final = "".join(parts)
        return final
