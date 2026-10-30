"""The records the zonekit modules pass to one another.

Every domain name in these records is absolute, lowercase and ends in a dot, written in
presentation form without escapes: `www.example.com.`. The root is `.`.
"""

import enum
from dataclasses import dataclass


class ZoneError(ValueError):
    """Input the zone tools cannot work with."""


class RType(enum.Enum):
    """A record type; the value is its RFC 1035 type code."""

    A = 1
    NS = 2
    CNAME = 5
    SOA = 6
    MX = 15
    TXT = 16
    AAAA = 28
    SRV = 33
    CAA = 257


# The only class zonekit handles, as written in a master file and as coded on the wire.
CLASS_IN = "IN"
CLASS_IN_CODE = 1


@dataclass(frozen=True)
class A:
    """An IPv4 address in dotted-quad form, such as `192.0.2.1`."""

    address: str


@dataclass(frozen=True)
class AAAA:
    """An IPv6 address in the compressed form Python's `ipaddress` writes, such as `2001:db8::1`."""

    address: str


@dataclass(frozen=True)
class CNAME:
    """The canonical name an alias points at."""

    target: str


@dataclass(frozen=True)
class NS:
    """A name server for the owner's zone."""

    target: str


@dataclass(frozen=True)
class MX:
    """A mail exchanger; lower preference is tried first."""

    preference: int
    exchange: str


@dataclass(frozen=True)
class TXT:
    """One or more character strings, each 0 to 255 bytes, escapes already resolved."""

    strings: tuple[bytes, ...]


@dataclass(frozen=True)
class SOA:
    """The start of authority. The five numbers are unsigned 32-bit; the times are seconds."""

    mname: str
    rname: str
    serial: int
    refresh: int
    retry: int
    expire: int
    minimum: int


@dataclass(frozen=True)
class SRV:
    """A service location (RFC 2782). A target of `.` means the service is not offered."""

    priority: int
    weight: int
    port: int
    target: str


@dataclass(frozen=True)
class CAA:
    """A certification authority authorization (RFC 8659). Flag 128 marks the tag critical."""

    flags: int
    tag: str
    value: bytes


Rdata = A | AAAA | CNAME | NS | MX | TXT | SOA | SRV | CAA


@dataclass(frozen=True)
class Record:
    """One resource record. `rtype` always names the type of `rdata`; `rclass` is CLASS_IN."""

    owner: str
    ttl: int
    rclass: str
    rtype: RType
    rdata: Rdata


@dataclass(frozen=True)
class Zone:
    """A zone's origin and its records, in the order the master file gives them."""

    origin: str
    records: tuple[Record, ...]


class Severity(enum.Enum):
    """How bad a finding is: an error breaks resolution, a warning is poor practice."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Problem:
    """A finding about a zone, on the records of one owner name."""

    severity: Severity
    owner: str
    message: str
