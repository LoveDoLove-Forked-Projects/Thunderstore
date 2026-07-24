from typing import Optional

from django.db import models
from django.db.models import Manager, Q, TextChoices

from thunderstore.core.mixins import TimestampMixin

from .community import Community


class CommunityAlertVariant(TextChoices):
    Info = "info"
    Warning = "warning"
    Danger = "danger"
    Success = "success"


class CommunityAlert(TimestampMixin):
    """
    An alert displayed at the top of the page to inform users of important
    information. Intended to replace the DynamicHTML system for this use case;
    the message is stored as markdown so hyperlinks (and other inline
    formatting) can be rendered safely by clients (new frontend, mod managers).
    """

    name = models.CharField(
        max_length=256,
        help_text="Internal identifier, not shown to users.",
    )
    message = models.TextField(
        help_text="Alert content as markdown. Supports hyperlinks.",
    )
    variant = models.CharField(
        max_length=64,
        choices=CommunityAlertVariant.choices,
        default=CommunityAlertVariant.Info,
    )
    ordering = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    exclude_communities = models.ManyToManyField(
        "community.Community",
        related_name="community_alert_exclusions",
        blank=True,
        help_text="Hidden from these communities.",
    )
    require_communities = models.ManyToManyField(
        "community.Community",
        related_name="community_alert_inclusions",
        blank=True,
        help_text="Shown only in these communities. If empty, shown everywhere.",
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("-ordering", "-pk")

    @classmethod
    def get_for_community(cls, community: Optional[Community]):
        if community:
            community_filter = Q(
                ~Q(exclude_communities=community)
                & Q(Q(require_communities=None) | Q(require_communities=community))
            )
        else:
            community_filter = Q(require_communities=None)

        return cls.objects.filter(
            Q(is_active=True) & community_filter,
        ).order_by("-ordering", "-pk")
