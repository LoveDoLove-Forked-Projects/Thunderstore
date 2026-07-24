from django.contrib import admin

from ..models.community_alert import CommunityAlert


@admin.register(CommunityAlert)
class CommunityAlertAdmin(admin.ModelAdmin):
    filter_horizontal = (
        "exclude_communities",
        "require_communities",
    )
    readonly_fields = (
        "datetime_created",
        "datetime_updated",
    )
    list_display = (
        "name",
        "variant",
        "ordering",
        "datetime_created",
        "datetime_updated",
        "is_active",
    )
    list_filter = (
        "is_active",
        "variant",
        "exclude_communities",
        "require_communities",
    )
    search_fields = ("name", "message")
