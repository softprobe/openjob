"""A company proves its owners with /.well-known/openjob.txt.

Maintainer review is the fallback when that file is missing or does not list
the owners. The live fetch is used only by the checker command. Tests pass
their own reader and do not touch the network.
"""

from __future__ import annotations

import ipaddress
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from indexer import USER_AGENT


def well_known_url(website: object) -> str | None:
    if not isinstance(website, str):
        return None
    parsed = urlsplit(website.strip())
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not _public_host(host):
        return None
    return f"https://{host}/.well-known/openjob.txt"


def logins_in(body: str) -> set[str]:
    found = set()
    for line in body.splitlines():
        login = line.split("#", 1)[0].strip()
        if login:
            found.add(login.casefold())
    return found


def owners_listed(meta: dict, body: str) -> bool:
    owners = meta.get("owners") or []
    if not isinstance(owners, list) or not owners:
        return False
    listed = logins_in(body)
    return all(str(owner).strip().casefold() in listed for owner in owners)


def fetch_well_known(url: str, *, timeout: float = 10) -> str:
    """GET one https URL. Redirects are refused. The body is capped."""
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or parsed.path != "/.well-known/openjob.txt" or not _public_host(host):
        return ""
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/plain"})
    opener = build_opener(_RefuseRedirects)
    try:
        with opener.open(request, timeout=timeout) as response:
            final = urlsplit(response.geturl())
            if (final.hostname or "").lower() != host or final.scheme != "https":
                raise ValueError("Refusing a claim response from a different host.")
            return response.read(10_000).decode("utf-8", "replace")
    except (HTTPError, URLError, TimeoutError, ValueError):
        return ""


class _RefuseRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ARG002
        raise ValueError("Refusing a redirect while checking a company claim.")


def _public_host(host: str) -> bool:
    if not host or host in {"localhost", "metadata.google.internal"} or host.endswith(".local"):
        return False
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return "." in host
    return False
