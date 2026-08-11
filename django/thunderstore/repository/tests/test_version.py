"""
Characterization tests for package version parsing, validation and ordering.

The expectations below were captured empirically from
``distutils.version.StrictVersion`` running on Python 3.8, before distutils was
replaced ahead of the Python 3.12 migration. They exist to prove the
replacement did not widen the grammar accepted at package submission time, and
did not reorder existing versions.

Treat a failure here as a behaviour regression, not a test that needs updating.
"""

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError

from thunderstore.repository.validators import VersionNumberValidator
from thunderstore.repository.version import Version

# Version strings the parser accepts, with the (version, prerelease) they
# produce. Note the parser is broader than VersionNumberValidator: it accepts
# two-component versions, leading zeros and a/b prereleases. PackageReference
# relies on this broader grammar, so it is preserved deliberately.
PARSER_ACCEPTS = (
    ("1.0.0", (1, 0, 0), None),
    ("0.0.0", (0, 0, 0), None),
    ("1.2.3", (1, 2, 3), None),
    ("10.20.30", (10, 20, 30), None),
    ("0.0.1", (0, 0, 1), None),
    ("999999.0.0", (999999, 0, 0), None),
    # Two-component form fills the patch with 0.
    ("1.0", (1, 0, 0), None),
    ("2.0", (2, 0, 0), None),
    # Leading zeros parse (the validator rejects them separately).
    ("01.0.0", (1, 0, 0), None),
    ("1.00.0", (1, 0, 0), None),
    ("00.00.00", (0, 0, 0), None),
    ("0001.0002.0003", (1, 2, 3), None),
    # Prerelease suffixes.
    ("1.0.0a1", (1, 0, 0), ("a", 1)),
    ("1.0.0b2", (1, 0, 0), ("b", 2)),
    ("1.0a1", (1, 0, 0), ("a", 1)),
    ("1.2.3a9", (1, 2, 3), ("a", 9)),
    # A single trailing newline is tolerated by the regex's "$" anchor.
    ("1.0.0\n", (1, 0, 0), None),
)

# Version strings the parser rejects, with the exact ValueError message. These
# messages reach users as validation errors on package submission.
PARSER_REJECTS = (
    ("1", "invalid version number '1'"),
    ("1.0.0.0", "invalid version number '1.0.0.0'"),
    ("1.2.3.4.5", "invalid version number '1.2.3.4.5'"),
    ("1.0.0 ", "invalid version number '1.0.0 '"),
    ("  1.0.0", "invalid version number '  1.0.0'"),
    ("1 .0.0", "invalid version number '1 .0.0'"),
    ("1.0.0-alpha", "invalid version number '1.0.0-alpha'"),
    ("1.0.0+build", "invalid version number '1.0.0+build'"),
    ("v1.0.0", "invalid version number 'v1.0.0'"),
    ("1.0.0.post1", "invalid version number '1.0.0.post1'"),
    ("1.0.0.dev0", "invalid version number '1.0.0.dev0'"),
    ("1!1.0.0", "invalid version number '1!1.0.0'"),
    ("a.b.c", "invalid version number 'a.b.c'"),
    ("1.0.0rc1", "invalid version number '1.0.0rc1'"),
    ("1.0.0c1", "invalid version number '1.0.0c1'"),
    ("1.0.0A1", "invalid version number '1.0.0A1'"),
    ("-1.0.0", "invalid version number '-1.0.0'"),
    ("1.-1.0", "invalid version number '1.-1.0'"),
    ("1.0.0 beta", "invalid version number '1.0.0 beta'"),
    ("1.0.0a", "invalid version number '1.0.0a'"),
    # Non-ASCII digits are rejected via the regex's re.ASCII flag.
    ("１.０.０", "invalid version number '１.０.０'"),
)


@pytest.mark.parametrize(("value", "expected", "prerelease"), PARSER_ACCEPTS)
def test_version_parser_accepts(value, expected, prerelease):
    version = Version(value)
    assert version.version == expected
    assert version.prerelease == prerelease


@pytest.mark.parametrize(("value", "message"), PARSER_REJECTS)
def test_version_parser_rejects(value, message):
    with pytest.raises(ValueError) as exc:
        Version(value)
    assert str(exc.value) == message


@pytest.mark.parametrize("value", ("", None))
def test_version_parser_rejects_empty(value):
    """
    Intentional deviation from StrictVersion.

    StrictVersion skipped parsing for falsy input and left the instance without
    a `version` attribute, so the failure surfaced later as an AttributeError
    from unrelated code. Both reject the input; this raises ValueError at
    construction, matching every other invalid version.
    """
    with pytest.raises(ValueError) as exc:
        Version(value)
    assert str(exc.value) == f"invalid version number '{value}'"


# Ordered strictly ascending. Ordering determines which version is surfaced as
# "latest" across the API and package pages.
ASCENDING = (
    "0.0.0",
    "0.0.1",
    "0.9.9",
    "1.0.0a1",
    "1.0.0a2",
    "1.0.0b1",
    "1.0.0",
    "1.0.9",
    "1.0.10",
    "1.2.0",
    "1.10.0",
    "2.0.0",
    "10.0.0",
)


def test_version_ordering_is_strictly_ascending():
    versions = [Version(v) for v in ASCENDING]
    for smaller, larger in zip(versions, versions[1:]):
        assert smaller < larger
        assert larger > smaller
        assert smaller != larger


def test_version_ordering_sorts_numerically_not_lexically():
    """1.0.10 must sort above 1.0.9, and 10.0.0 above 2.0.0."""
    shuffled = ["1.0.10", "10.0.0", "1.0.9", "2.0.0", "1.2.0"]
    assert sorted(shuffled, key=Version) == [
        "1.0.9",
        "1.0.10",
        "1.2.0",
        "2.0.0",
        "10.0.0",
    ]


def test_prerelease_sorts_below_final_release():
    assert Version("1.0.0a1") < Version("1.0.0")
    assert Version("1.0.0b1") < Version("1.0.0")
    assert Version("1.0.0a1") < Version("1.0.0b1")


def test_two_component_equals_three_component():
    assert Version("1.0") == Version("1.0.0")


def test_version_compares_against_plain_strings():
    assert Version("1.0.0") == "1.0.0"
    assert Version("1.0.0") < "1.0.1"


def test_version_returns_notimplemented_for_other_types():
    assert Version("1.0.0").__eq__(5) is NotImplemented
    assert Version("1.0.0").__lt__(object()) is NotImplemented


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        # StrictVersion drops a zero patch component when stringifying. Kept
        # for fidelity; call sites needing the canonical form join .version.
        ("1.0.0", "1.0"),
        ("1.2.3", "1.2.3"),
        ("1.0.0a1", "1.0a1"),
    ),
)
def test_version_str_matches_strictversion(value, expected):
    assert str(Version(value)) == expected


def test_canonical_string_is_built_from_version_tuple():
    """The form used by PackageReference.version_str and the validator."""
    assert ".".join(str(x) for x in Version("1.0.0").version) == "1.0.0"


# The validator is stricter than the parser: it additionally requires the input
# to round-trip to canonical major.minor.patch. Messages are user-facing.
VALIDATOR_ACCEPTS = ("1.0.0", "0.0.0", "1.2.3", "10.20.30", "0.0.1", "999999.0.0")

VALIDATOR_REJECTS = (
    ("1.0", "Version 1.0 should be written as 1.0.0"),
    ("2.0", "Version 2.0 should be written as 2.0.0"),
    ("01.0.0", "Version 01.0.0 should be written as 1.0.0"),
    ("1.00.0", "Version 1.00.0 should be written as 1.0.0"),
    ("1.0.00", "Version 1.0.00 should be written as 1.0.0"),
    ("00.00.00", "Version 00.00.00 should be written as 0.0.0"),
    ("0001.0002.0003", "Version 0001.0002.0003 should be written as 1.2.3"),
    ("1.0.0a1", "Version 1.0.0a1 should be written as 1.0.0"),
    ("1.0.0b2", "Version 1.0.0b2 should be written as 1.0.0"),
    ("1.0a1", "Version 1.0a1 should be written as 1.0.0"),
    ("1", "invalid version number '1'"),
    ("1.0.0.0", "invalid version number '1.0.0.0'"),
    ("v1.0.0", "invalid version number 'v1.0.0'"),
    ("1.0.0.post1", "invalid version number '1.0.0.post1'"),
    ("a.b.c", "invalid version number 'a.b.c'"),
    ("1.0.0rc1", "invalid version number '1.0.0rc1'"),
    ("20.08.210338", "Version 20.08.210338 should be written as 20.8.210338"),
)


@pytest.mark.parametrize("value", VALIDATOR_ACCEPTS)
def test_version_number_validator_accepts(value):
    VersionNumberValidator()(value)


@pytest.mark.parametrize(("value", "message"), VALIDATOR_REJECTS)
def test_version_number_validator_rejects(value, message):
    with pytest.raises(DjangoValidationError) as exc:
        VersionNumberValidator()(value)
    assert message in str(exc.value)


@pytest.mark.parametrize("value", ("", None))
def test_version_number_validator_rejects_empty(value):
    """
    Previously raised an uncaught AttributeError rather than a ValidationError,
    because StrictVersion left `.version` unset for falsy input and the
    validator only caught ValueError. Now rejected properly.
    """
    with pytest.raises(DjangoValidationError):
        VersionNumberValidator()(value)
