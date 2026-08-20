"""
A faithful in-repo replacement for ``distutils.version.StrictVersion``, which
was removed from the standard library in Python 3.12 (PEP 632). Version parsing
is user-facing at package submission and determines "latest version"
resolution, so grammar, ordering and error messages are reproduced exactly;
tests/test_version.py holds the characterization suite.

``packaging.version.Version`` is deliberately not used: it accepts a far wider
grammar (PEP 440) and orders suffixed versions differently.

One deviation: empty or ``None`` input raises ``ValueError`` at construction
instead of surfacing later as an ``AttributeError``. Instances are unhashable
like ``StrictVersion`` and must stay that way, as they compare equal to their
string form.
"""

import re
from typing import Any, Optional, Tuple

VERSION_RE = re.compile(r"^(\d+) \. (\d+) (\. (\d+))? ([ab](\d+))?$", re.VERBOSE)


class Version:
    """
    A strict ``major.minor.patch`` version with an optional ``aN``/``bN``
    prerelease suffix.
    """

    version: Tuple[int, int, int]
    prerelease: Optional[Tuple[str, int]]

    def __init__(self, vstring: Optional[str] = None) -> None:
        self.parse(vstring)

    def parse(self, vstring: Optional[str]) -> None:
        if not vstring:
            raise ValueError(f"invalid version number '{vstring}'")

        match = VERSION_RE.match(vstring)
        if not match:
            raise ValueError(f"invalid version number '{vstring}'")

        (major, minor, patch, prerelease, prerelease_num) = match.group(1, 2, 4, 5, 6)

        if patch:
            self.version = (int(major), int(minor), int(patch))
        else:
            self.version = (int(major), int(minor), 0)

        if prerelease:
            self.prerelease = (prerelease[0], int(prerelease_num))
        else:
            self.prerelease = None

    def __str__(self) -> str:
        if self.version[2] == 0:
            vstring = ".".join(str(x) for x in self.version[0:2])
        else:
            vstring = ".".join(str(x) for x in self.version)

        if self.prerelease:
            vstring = vstring + self.prerelease[0] + str(self.prerelease[1])

        return vstring

    def __repr__(self) -> str:
        return f"Version ('{self!s}')"

    def _cmp(self, other: Any) -> Any:
        if isinstance(other, str):
            other = Version(other)
        elif not isinstance(other, Version):
            return NotImplemented

        if self.version != other.version:
            return -1 if self.version < other.version else 1

        if not self.prerelease and not other.prerelease:
            return 0
        elif self.prerelease and not other.prerelease:
            return -1
        elif not self.prerelease and other.prerelease:
            return 1

        if self.prerelease == other.prerelease:
            return 0
        return -1 if self.prerelease < other.prerelease else 1

    def __eq__(self, other: Any) -> Any:
        result = self._cmp(other)
        if result is NotImplemented:
            return result
        return result == 0

    def __lt__(self, other: Any) -> Any:
        result = self._cmp(other)
        if result is NotImplemented:
            return result
        return result < 0

    def __le__(self, other: Any) -> Any:
        result = self._cmp(other)
        if result is NotImplemented:
            return result
        return result <= 0

    def __gt__(self, other: Any) -> Any:
        result = self._cmp(other)
        if result is NotImplemented:
            return result
        return result > 0

    def __ge__(self, other: Any) -> Any:
        result = self._cmp(other)
        if result is NotImplemented:
            return result
        return result >= 0
