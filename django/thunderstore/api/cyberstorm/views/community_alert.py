from rest_framework.generics import ListAPIView, get_object_or_404

from thunderstore.api.cyberstorm.serializers import CyberstormCommunityAlertSerializer
from thunderstore.api.utils import CyberstormAutoSchemaMixin, PublicCacheMixin
from thunderstore.community.models import Community, CommunityAlert


class CommunityAlertListAPIView(
    PublicCacheMixin, CyberstormAutoSchemaMixin, ListAPIView
):
    """
    Return the active alerts to display at the top of the given community's
    main page.
    """

    serializer_class = CyberstormCommunityAlertSerializer
    cache_max_age = 60 * 5  # 5 minutes

    def get_queryset(self):
        community = get_object_or_404(
            Community.objects.all(),
            identifier=self.kwargs["community_id"],
        )
        return CommunityAlert.get_for_community(community)
