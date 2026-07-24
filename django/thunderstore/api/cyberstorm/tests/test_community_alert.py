import pytest
from rest_framework.test import APIClient

from thunderstore.community.factories import CommunityFactory
from thunderstore.community.models import CommunityAlert, CommunitySite


@pytest.mark.django_db
def test_api_cyberstorm_community_alerts_success(
    client: APIClient,
    community_site: CommunitySite,
):
    community = community_site.community
    other_community = CommunityFactory()

    # Shown: site-wide (no targeting) and required for this community.
    site_wide = CommunityAlert.objects.create(
        name="Site wide",
        message="Everywhere [link](https://example.com)",
        variant="info",
        ordering=0,
    )
    required = CommunityAlert.objects.create(
        name="Required",
        message="This community only",
        variant="warning",
        ordering=10,
    )
    required.require_communities.set([community])

    # Hidden: inactive, required elsewhere, and explicitly excluded here.
    CommunityAlert.objects.create(name="Inactive", message="nope", is_active=False)
    other = CommunityAlert.objects.create(name="Other", message="nope")
    other.require_communities.set([other_community])
    excluded = CommunityAlert.objects.create(name="Excluded", message="nope")
    excluded.exclude_communities.set([community])

    response = client.get(
        f"/api/cyberstorm/community/{community.identifier}/alerts/",
        HTTP_HOST=community_site.site.domain,
    )
    assert response.status_code == 200
    data = response.json()

    # Only the two visible alerts, ordered by -ordering (required before site_wide).
    assert [a["id"] for a in data] == [required.pk, site_wide.pk]

    first = data[0]
    assert first["message"] == required.message
    assert first["variant"] == "warning"
    assert set(first.keys()) == {
        "id",
        "message",
        "variant",
        "datetime_created",
        "datetime_updated",
    }


@pytest.mark.django_db
def test_api_cyberstorm_community_alerts_empty(
    client: APIClient,
    community_site: CommunitySite,
):
    response = client.get(
        f"/api/cyberstorm/community/{community_site.community.identifier}/alerts/",
        HTTP_HOST=community_site.site.domain,
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
def test_api_cyberstorm_community_alerts_unknown_community(
    client: APIClient,
    community_site: CommunitySite,
):
    response = client.get(
        "/api/cyberstorm/community/does-not-exist/alerts/",
        HTTP_HOST=community_site.site.domain,
    )
    assert response.status_code == 404
