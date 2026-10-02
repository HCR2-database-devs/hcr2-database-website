import ipaddress
from typing import Any


def canonicalize_client_ip(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        address = ipaddress.ip_address(value.strip())
    except ValueError:
        return None
    if isinstance(address, ipaddress.IPv6Address):
        if address.scope_id is not None:
            return None
        if address.ipv4_mapped is not None:
            address = address.ipv4_mapped
    return address.compressed


def trusted_client_ip(request: Any) -> str | None:
    client = getattr(request, "client", None)
    return canonicalize_client_ip(getattr(client, "host", None))
