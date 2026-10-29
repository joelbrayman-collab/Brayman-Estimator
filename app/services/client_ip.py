"""The signer's IP address for signing evidence (PP-2, 29 Oct 2026).

Hosted Live runs on Render. Every request to a public Render web service passes through Cloudflare and then Render's
load balancer, so the socket address the app sees (``request.remote_addr``) is a Render-internal proxy, and
``X-Forwarded-For`` keeps whatever the sender wrote at its left (Render appends; it does not reset it). Cloudflare sets
``CF-Connecting-IP`` to the address that connected to Cloudflare and refuses a request that tries to supply it itself.

So, only when the app knows it runs on Render (Render sets ``RENDER=true``) or is configured with
``CLIENT_IP_HEADER``, the signer's address is taken from that header, if it holds a valid IP address. Otherwise (local,
tests, the training site on HostPapa, or the header missing or malformed) it is the socket address, as before.
``X-Forwarded-For`` is never trusted. Nothing here blocks a request: it only decides what is recorded.
"""

from __future__ import annotations

import ipaddress
import os
from typing import Optional

from flask import current_app, has_request_context, request

RENDER_CLIENT_IP_HEADER = "CF-Connecting-IP"


def trusted_client_ip_header() -> Optional[str]:
    configured = (current_app.config.get("CLIENT_IP_HEADER") or "").strip()
    if configured:
        return configured
    if os.environ.get("RENDER") == "true":
        return RENDER_CLIENT_IP_HEADER
    return None


def _valid(value: str) -> Optional[str]:
    try:
        return str(ipaddress.ip_address((value or "").strip()))
    except ValueError:
        return None


def request_client_ip() -> Optional[str]:
    """The originating client address as far as the hosting proxy vouches for it; else the socket address."""
    if not has_request_context():
        return None
    header = trusted_client_ip_header()
    if header:
        vouched = _valid(request.headers.get(header, ""))
        if vouched:
            return vouched
    return request.remote_addr or None
