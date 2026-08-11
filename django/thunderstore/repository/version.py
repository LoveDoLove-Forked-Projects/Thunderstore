"""
A faithful in-repo replacement for ``distutils.version.StrictVersion``.

``distutils`` was removed from the standard library in Python 3.12 (PEP 632).
Package version strings are user-facing at submission time and determine
"latest version" resolution, so this module reproduces ``StrictVersion``'s
parsing grammar, ordering semantics and error message text exactly rather than
approximating them.

``packaging.version.Version`` is deliberately NOT used as the replacement. It
accepts a far wider grammar (``1.0``, ``1.0.0.post1``, ``1.0.0.dev0``, epochs,
local versions), which would silently widen what can be submitted to the
package index, and it orders suffixed versions differently.

Two intentional deviations from ``StrictVersion``, both strictly safer:

1. An empty or ``None`` version string raises ``ValueError``. ``StrictVersion``
   skipped parsing entirely for falsy input, leaving the instance without a
   ``version`` attribute so the failure surfaced later as an ``AttributeError``
   from unrelated code. Both reject the input; this one rejects it at
   construction using the same exception type as every other invalid version.
2. Instances are hashable. ``StrictVersion`` defined ``__eq__`` without
   ``__hash__`` and was therefore unhashable.
"""

import re
from typing import Any, Optional, Tuple, Union

# Mirrors distutils.version.StrictVersion.version_re exactly.
VERSION_RE = re.compile(
    r"^(\d+) \. (\d+) (\. (\d+))? ([ab](\d+))?$", re.VERBOSE | re.ASCII
)


class Version:
    """
    A strict ``major.minor.patch`` version, optionally carrying an ``aN``/``bN``
    prerelease suffix.

    Note that the patch component is optional when parsing (``1.0`` parses to
    ``(1, 0, 0)``); callers that require the canonical three-component form must
    check the round-trip themselves, as ``VersionNumberValidator`` does.
    """

    version: Tuple[int, int, int]
    prerelease: Optional[Tuple[str, int]]

    def __init__(self, vstring: Optional[str] = None) -> None:
        self.parse(vstring)

    def parse(self, vstring: Optional[str]) -> None:
        # StrictVersion silently skipped parsing for falsy input, leaving
        # self.version unset. Reject it up front instead; see module docstring.
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
        # Faithful to StrictVersion, including its quirk of dropping a zero
        # patch component: str(Version("1.0.0")) == "1.0". Callers that need the
        # canonical three-component string should join self.version instead.
        if self.version[2] == 0:
            vstring = ".".join(str(x) for x in self.version[0:2])
        else:
            vstring = ".".join(str(x) for x in self.version)

        if self.prerelease:
            vstring = vstring + self.prerelease[0] + str(self.prerelease[1])

        return vstring

    def __repr__(self) -> str:
        return f"Version ('{str(self)}')"

    def _cmp(self, other: Any) -> Any:
        if isinstance(other, str):
            other = Version(other)
        elif not isinstance(other, Version):
            return NotImplemented

        if self.version != other.version:
            return -1 if self.version < other.version else 1

        # Numeric components are equal, so the prerelease decides. A version
        # carrying a prerelease sorts before the same version without one.
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

    def __hash__(self) -> int:
        return hash((self.version, self.prerelease))


def to_version(value: Union[str, Version]) -> Version:
    """Coerce a version string into a Version, passing existing ones through."""
    if isinstance(value, Version):
        return value
    return Version(value)
