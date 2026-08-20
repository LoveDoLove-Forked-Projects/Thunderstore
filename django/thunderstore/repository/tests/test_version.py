"""
Characterization tests captured from distutils.version.StrictVersion on
Python 3.8. Treat a failure here as a behaviour regression, not a test that
needs updating.
"""

from itertools import pairwise

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError

from thunderstore.repository.validators import VersionNumberValidator
from thunderstore.repository.version import Version

PARSER_ACCEPTS = (
    ("1.0.0", (1, 0, 0), None),
    ("0.0.0", (0, 0, 0), None),
    ("1.2.3", (1, 2, 3), None),
    ("10.20.30", (10, 20, 30), None),
    ("0.0.1", (0, 0, 1), None),
    ("999999.0.0", (999999, 0, 0), None),
    ("1.0", (1, 0, 0), None),
    ("2.0", (2, 0, 0), None),
    ("01.0.0", (1, 0, 0), None),
    ("1.00.0", (1, 0, 0), None),
    ("00.00.00", (0, 0, 0), None),
    ("0001.0002.0003", (1, 2, 3), None),
    ("1.0.0a1", (1, 0, 0), ("a", 1)),
    ("1.0.0b2", (1, 0, 0), ("b", 2)),
    ("1.0a1", (1, 0, 0), ("a", 1)),
    ("1.2.3a9", (1, 2, 3), ("a", 9)),
    ("1.0.0\n", (1, 0, 0), None),
)

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
    ("１.０.０", "invalid version number '１.０.０'"),  # noqa: RUF001
    ("١.٠.٠", "invalid version number '١.٠.٠'"),
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
    with pytest.raises(ValueError) as exc:
        Version(value)
    assert str(exc.value) == f"invalid version number '{value}'"


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
    for smaller, larger in pairwise(versions):
        assert smaller < larger
        assert larger > smaller
        assert smaller != larger


def test_version_ordering_sorts_numerically_not_lexically():
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


def test_version_supports_all_comparison_operators():
    assert Version("1.0.0") == Version("1.0.0")
    assert Version("1.0.0") != Version("1.0.1")
    assert Version("1.0.0") < Version("1.0.1")
    assert Version("1.0.0") <= Version("1.0.0")
    assert Version("1.0.0") <= Version("1.0.1")
    assert Version("1.0.1") > Version("1.0.0")
    assert Version("1.0.0") >= Version("1.0.0")
    assert Version("1.0.1") >= Version("1.0.0")
    assert Version("1.0.0a1") == Version("1.0.0a1")
    assert Version("1.0.0a1") != Version("1.0.0a2")
    assert Version("1.0.0a1") < Version("1.0.0a2")
    assert Version("1.0.0a1") <= Version("1.0.0a2")


def test_version_returns_notimplemented_for_other_types():
    assert Version("1.0.0").__eq__(5) is NotImplemented
    assert Version("1.0.0").__lt__(object()) is NotImplemented
    assert Version("1.0.0").__le__(object()) is NotImplemented
    assert Version("1.0.0").__gt__(object()) is NotImplemented
    assert Version("1.0.0").__ge__(object()) is NotImplemented


def test_version_is_unhashable():
    with pytest.raises(TypeError, match="unhashable"):
        hash(Version("1.0.0"))


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("1.0.0", "1.0"),
        ("1.2.3", "1.2.3"),
        ("1.0.0a1", "1.0a1"),
    ),
)
def test_version_str_matches_strictversion(value, expected):
    assert str(Version(value)) == expected


def test_canonical_string_is_built_from_version_tuple():
    assert ".".join(str(x) for x in Version("1.0.0").version) == "1.0.0"


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
    ("１.０.０", "invalid version number '１.０.０'"),  # noqa: RUF001
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
    with pytest.raises(DjangoValidationError):
        VersionNumberValidator()(value)
