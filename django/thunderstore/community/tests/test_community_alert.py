from typing import List, Optional

import pytest

from thunderstore.community.factories import CommunityFactory
from thunderstore.community.models import CommunityAlert


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("required", "excluded", "target", "should_match"),
    (
        # No targeting: shown in every community and site-wide.
        ([], [], "community-a", True),
        ([], [], None, True),
        # Required communities: shown only where required.
        (["community-a"], [], "community-a", True),
        (["community-a"], [], "community-b", False),
        (["community-a", "community-b"], [], "community-b", True),
        # A required alert is not site-wide (no community context).
        (["community-a"], [], None, False),
        # Excluded communities: hidden there, shown elsewhere.
        ([], ["community-a"], "community-a", False),
        ([], ["community-a"], "community-b", True),
        ([], ["community-a"], None, True),
        # Exclusion wins over inclusion for the same community.
        (["community-a"], ["community-a"], "community-a", False),
    ),
)
def test_community_alert_community_filtering(
    required: List[str],
    excluded: List[str],
    target: Optional[str],
    should_match: bool,
):
    identifiers = set().union((*required, *excluded, *([target] if target else [])))
    communities = {
        identifier: CommunityFactory(identifier=identifier)
        for identifier in identifiers
    }

    alert = CommunityAlert.objects.create(name="Test alert", message="Hello")
    alert.require_communities.set([communities[x] for x in required])
    alert.exclude_communities.set([communities[x] for x in excluded])

    target_community = communities[target] if target else None
    matches = CommunityAlert.get_for_community(target_community)

    if should_match:
        assert matches.count() == 1
        assert matches.first() == alert
    else:
        assert matches.count() == 0


@pytest.mark.django_db
def test_community_alert_inactive_is_excluded():
    community = CommunityFactory()
    CommunityAlert.objects.create(
        name="Inactive",
        message="Hidden",
        is_active=False,
    )

    assert CommunityAlert.get_for_community(community).count() == 0
    assert CommunityAlert.get_for_community(None).count() == 0


@pytest.mark.django_db
def test_community_alert_ordering():
    community = CommunityFactory()
    low = CommunityAlert.objects.create(name="Low", message="a", ordering=0)
    high = CommunityAlert.objects.create(name="High", message="b", ordering=10)
    mid = CommunityAlert.objects.create(name="Mid", message="c", ordering=5)
    # Same ordering as `high`, created later => higher pk, so it sorts first.
    high_newer = CommunityAlert.objects.create(
        name="HighNewer", message="d", ordering=10
    )

    result = list(CommunityAlert.get_for_community(community))

    # Ordered by -ordering, then -pk (newest first) as the tiebreak.
    assert result == [high_newer, high, mid, low]
