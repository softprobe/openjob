"""schema.org objects for permalinks.

JobPosting is only for a job leaf page. Countries are emitted when the free-text
location names a US state, a country, or a city in the table below. Anything
else is omitted rather than guessed. ``employmentType`` and ``baseSalary`` are
omitted until a post has structured fields for them. ``TELECOMMUTE`` is used
only when ``remote`` is fully remote, never for hybrid.
"""

from __future__ import annotations

import json
import re
from typing import Mapping

_US_STATE = {
    "al": "AL", "ak": "AK", "az": "AZ", "ar": "AR", "ca": "CA", "co": "CO", "ct": "CT",
    "de": "DE", "dc": "DC", "fl": "FL", "ga": "GA", "hi": "HI", "id": "ID", "il": "IL",
    "in": "IN", "ia": "IA", "ks": "KS", "ky": "KY", "la": "LA", "me": "ME", "md": "MD",
    "ma": "MA", "mi": "MI", "mn": "MN", "ms": "MS", "mo": "MO", "mt": "MT", "ne": "NE",
    "nv": "NV", "nh": "NH", "nj": "NJ", "nm": "NM", "ny": "NY", "nc": "NC", "nd": "ND",
    "oh": "OH", "ok": "OK", "or": "OR", "pa": "PA", "ri": "RI", "sc": "SC", "sd": "SD",
    "tn": "TN", "tx": "TX", "ut": "UT", "vt": "VT", "va": "VA", "wa": "WA", "wv": "WV",
    "wi": "WI", "wy": "WY",
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV", "wisconsin": "WI",
    "wyoming": "WY", "district of columbia": "DC",
}
_COUNTRY = {
    "us": "US", "usa": "US", "u.s.": "US", "u.s.a.": "US",
    "united states": "US", "united states of america": "US", "america": "US",
    "cn": "CN", "china": "CN", "prc": "CN", "people's republic of china": "CN",
    "uk": "GB", "u.k.": "GB", "united kingdom": "GB", "great britain": "GB", "england": "GB",
    "canada": "CA", "germany": "DE", "france": "FR", "japan": "JP", "singapore": "SG",
    "india": "IN", "australia": "AU", "netherlands": "NL", "ireland": "IE",
}
_COUNTRY_NAME = {
    "US": "United States", "CN": "China", "GB": "United Kingdom", "CA": "Canada",
    "DE": "Germany", "FR": "France", "JP": "Japan", "SG": "Singapore", "IN": "India",
    "AU": "Australia", "NL": "Netherlands", "IE": "Ireland",
}
# Used only when the segment is exactly this city and no state or country was parsed.
_CITY = {
    "shanghai": ("Shanghai", None, "CN"),
    "beijing": ("Beijing", None, "CN"),
    "shenzhen": ("Shenzhen", None, "CN"),
    "hangzhou": ("Hangzhou", None, "CN"),
    "guangzhou": ("Guangzhou", None, "CN"),
    "singapore": ("Singapore", None, "SG"),
    "london": ("London", None, "GB"),
    "tokyo": ("Tokyo", None, "JP"),
    "san francisco": ("San Francisco", "CA", "US"),
    "los altos": ("Los Altos", "CA", "US"),
    "new york": ("New York", "NY", "US"),
    "seattle": ("Seattle", "WA", "US"),
    "austin": ("Austin", "TX", "US"),
    "boston": ("Boston", "MA", "US"),
}


def places_for(location: object) -> list[dict[str, str]]:
    """Places with a known country. Each item has country and maybe locality and region."""
    if not isinstance(location, str) or not location.strip():
        return []
    found: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for part in re.split(r"\s+/\s+|\s+\|\s+", location):
        place = _place(part.strip(" ,;"))
        if place is None:
            continue
        key = (place.get("locality", ""), place.get("region", ""), place["country"])
        if key in seen:
            continue
        seen.add(key)
        found.append(place)
    return found


def script_tag(data: object) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return f'<script type="application/ld+json">{payload}</script>'


def post_jsonld(post: Mapping[str, object], description_html: str, body: str = "") -> str:
    kind = str(post.get("kind") or "")
    graph: list[dict] = [breadcrumb(post)]
    if kind == "job":
        graph.insert(0, job_posting(post, description_html, body))
    elif kind == "company":
        graph.insert(0, organization(post))
    elif kind in {"talent", "talent-ref"}:
        graph.insert(0, person(post))
    return script_tag({"@context": "https://schema.org", "@graph": graph})


def website_jsonld(origin: str, description: str) -> dict:
    home = origin.rstrip("/") + "/"
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "OpenJob",
        "url": home,
        "description": description,
        "publisher": {
            "@type": "Organization",
            "name": "OpenJob",
            "url": home,
            "sameAs": "https://github.com/softprobe/openjob",
        },
    }


def job_posting(post: Mapping[str, object], description_html: str, body: str = "") -> dict:
    data: dict = {
        "@type": "JobPosting",
        "title": post.get("title") or "",
        "description": description_html,
        "datePosted": post.get("posted") or "",
        "hiringOrganization": _hiring_org(post),
        "identifier": {
            "@type": "PropertyValue",
            "name": "OpenJob",
            "value": str(post.get("path") or "").removesuffix(".md"),
        },
        "url": post.get("permalink") or "",
        "directApply": _direct_apply(post, body),
    }
    expires = post.get("expires")
    if isinstance(expires, str) and expires:
        data["validThrough"] = f"{expires}T23:59:59Z"
    places = places_for(post.get("location"))
    remote = post.get("remote")
    if remote == "remote":
        data["jobLocationType"] = "TELECOMMUTE"
        countries = []
        seen: set[str] = set()
        for place in places:
            code = place["country"]
            if code in seen:
                continue
            seen.add(code)
            countries.append({"@type": "Country", "name": _COUNTRY_NAME.get(code, code)})
        if len(countries) == 1:
            data["applicantLocationRequirements"] = countries[0]
        elif countries:
            data["applicantLocationRequirements"] = countries
    elif places:
        data["jobLocation"] = [_place_node(place) for place in places]
    action = _apply_action(post)
    if action:
        data["potentialAction"] = action
    return data


def organization(post: Mapping[str, object]) -> dict:
    data: dict = {"@type": "Organization", "name": post.get("title") or post.get("org") or ""}
    website = _https(post.get("org_website")) or _https(post.get("website"))
    if website:
        data["url"] = website
        data["sameAs"] = website
    logo = _https(post.get("logo"))
    if logo:
        data["logo"] = logo
    return data


def person(post: Mapping[str, object]) -> dict:
    data: dict = {"@type": "Person", "name": post.get("title") or ""}
    headline = post.get("headline")
    if isinstance(headline, str) and headline:
        data["jobTitle"] = headline
    same: list[str] = []
    owner = post.get("owner")
    if isinstance(owner, str) and owner:
        same.append(f"https://github.com/{owner}")
    for key in ("website", "linkedin", "profile_url"):
        url = _https(post.get(key))
        if url and url not in same:
            same.append(url)
    if same:
        data["sameAs"] = same
    return data


def breadcrumb(post: Mapping[str, object]) -> dict:
    from validator.share import PAGES_ORIGIN

    home = PAGES_ORIGIN.rstrip("/") + "/"
    kind = str(post.get("kind") or "")
    section = {"job": "Jobs", "company": "Companies", "talent": "Talent", "talent-ref": "Talent"}.get(kind, "Posts")
    title = str(post.get("title") or "Post")
    permalink = str(post.get("permalink") or home)
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "OpenJob", "item": home},
            {"@type": "ListItem", "position": 2, "name": section, "item": home},
            {"@type": "ListItem", "position": 3, "name": title, "item": permalink},
        ],
    }


def _hiring_org(post: Mapping[str, object]) -> dict:
    org: dict = {"@type": "Organization", "name": post.get("org") or post.get("title") or ""}
    website = _https(post.get("org_website"))
    if website:
        org["url"] = website
        org["sameAs"] = website
    logo = _https(post.get("logo"))
    if logo:
        org["logo"] = logo
    return org


def _direct_apply(post: Mapping[str, object], body: str) -> bool:
    """True when the page itself shows how to reach the employer.

    An off-site ATS link alone is not direct apply. The generated Apply button
    does not count. An on-page hiring address, or instructions the author wrote,
    does.
    """
    if post.get("apply_email"):
        return True
    return bool(re.search(r"how to apply|如何申请", body, re.IGNORECASE))


def _apply_action(post: Mapping[str, object]) -> dict | None:
    target = _https(post.get("apply"))
    if target is None and isinstance(post.get("apply_email"), str):
        email = str(post["apply_email"])
        if email.startswith("mailto:"):
            target = email
    if target is None:
        return None
    return {"@type": "ApplyAction", "target": target}


def _place_node(place: dict[str, str]) -> dict:
    address: dict[str, str] = {"@type": "PostalAddress", "addressCountry": place["country"]}
    if place.get("locality"):
        address["addressLocality"] = place["locality"]
    if place.get("region"):
        address["addressRegion"] = place["region"]
    return {"@type": "Place", "address": address}


def _place(segment: str) -> dict[str, str] | None:
    if not segment:
        return None
    bits = [bit.strip() for bit in segment.split(",") if bit.strip()]
    if len(bits) >= 2:
        country = _COUNTRY.get(bits[-1].lower())
        region = _US_STATE.get(bits[-2].lower()) if len(bits) >= 3 else _US_STATE.get(bits[-1].lower())
        if region and (country in {None, "US"}):
            return {"locality": bits[0], "region": region, "country": "US"}
        if country and len(bits) >= 2 and region is None:
            return {"locality": bits[0], "country": country}
        if country and region:
            return {"locality": bits[0], "region": region, "country": country}
    city = _CITY.get(segment.lower())
    if city:
        locality, region, country = city
        place = {"locality": locality, "country": country}
        if region:
            place["region"] = region
        return place
    country_only = _COUNTRY.get(segment.lower())
    if country_only:
        return {"country": country_only}
    return None


def _https(value: object) -> str | None:
    if isinstance(value, str) and value.startswith("https://") and not any(char.isspace() for char in value):
        return value
    return None
