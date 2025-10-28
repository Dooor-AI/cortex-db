"""Parse CortexDB connection strings.

Format: cortexdb://[api_key@]host[:port]

Examples:
    - cortexdb://localhost:8000
    - cortexdb://my_key@localhost:8000
    - cortexdb://my_key@api.cortexdb.com
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedConnection:
    """Parsed connection string."""

    base_url: str
    api_key: Optional[str] = None


def parse_connection_string(connection_string: str) -> ParsedConnection:
    """Parse a CortexDB connection string.

    Args:
        connection_string: Connection string in format cortexdb://[api_key@]host[:port]

    Returns:
        Parsed connection options

    Raises:
        ValueError: If connection string is invalid

    Examples:
        >>> parse_connection_string('cortexdb://localhost:8000')
        ParsedConnection(base_url='http://localhost:8000', api_key=None)

        >>> parse_connection_string('cortexdb://my_key@localhost:8000')
        ParsedConnection(base_url='http://localhost:8000', api_key='my_key')

        >>> parse_connection_string('cortexdb://key@api.cortexdb.com:443')
        ParsedConnection(base_url='https://api.cortexdb.com:443', api_key='key')
    """
    # Remove cortexdb:// prefix
    if not connection_string.startswith("cortexdb://"):
        raise ValueError('Connection string must start with "cortexdb://"')

    without_protocol = connection_string[len("cortexdb://") :]

    # Split by @ to separate api_key from host
    api_key: Optional[str] = None
    host_part: str

    if "@" in without_protocol:
        parts = without_protocol.split("@")
        if len(parts) != 2:
            raise ValueError("Invalid connection string format")
        api_key = parts[0]
        host_part = parts[1]
    else:
        host_part = without_protocol

    # Parse host and port
    port: Optional[str] = None

    if ":" in host_part:
        host_port_parts = host_part.split(":")
        host = host_port_parts[0]
        port = host_port_parts[1]
    else:
        host = host_part

    # Determine protocol (https for port 443 or production domains, http otherwise)
    is_secure = (
        port == "443"
        or "cortexdb.com" in host
        or (not host.startswith("localhost") and not host.startswith("127."))
    )

    protocol = "https" if is_secure else "http"

    # Build base URL
    base_url = f"{protocol}://{host}"
    if port and not (port == "443" and is_secure) and not (port == "80" and not is_secure):
        base_url += f":{port}"

    return ParsedConnection(base_url=base_url, api_key=api_key)

