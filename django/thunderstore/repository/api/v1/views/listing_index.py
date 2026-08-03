from django.shortcuts import get_object_or_404, redirect
from django.utils.cache import get_conditional_response
from django.utils.http import http_date
from drf_yasg import openapi  # type: ignore
from drf_yasg.utils import swagger_auto_schema  # type: ignore
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from thunderstore.community.models import Community
from thunderstore.core.utils import replace_cdn
from thunderstore.repository.models import APIV1ChunkedPackageCache

DESCRIPTION = (
    "Redirects to a gzip compressed blob file containing an array of URLs. "
    "Each URL points to a gzip compressed chunk of the community's package "
    "listing, in the same format as the `/api/v1/package/` endpoint.\n\n"
    "The response supports conditional requests via the `If-Modified-Since` "
    "header, in which case a 304 is returned instead of a redirect."
)

CDN_PARAMETER = openapi.Parameter(
    "cdn",
    openapi.IN_QUERY,
    description=("Hostname of a mirror CDN to serve the index blob from."),
    type=openapi.TYPE_STRING,
    required=False,
)


class PackageListingIndex(APIView):
    """
    Return a blob file containing URLs to package listing chunks.
    Client needs to gunzip and JSON parse the blob contents.

    /c/{community_id}/api/v1/package-listing-index/
    """

    @swagger_auto_schema(
        tags=["v1"],
        operation_description=DESCRIPTION,
        manual_parameters=[CDN_PARAMETER],
        responses={
            200: None,
            302: openapi.Response(
                description="Redirect to the index blob containing chunk URLs.",
            ),
            304: openapi.Response(
                description="The index has not changed since If-Modified-Since.",
            ),
            503: openapi.Response(
                description="No cache has been built for the community yet.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"error": openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
        },
    )
    def get(self, request: Request, community_identifier: str):
        community = get_object_or_404(
            Community.objects,
            identifier=community_identifier,
        )
        cache = APIV1ChunkedPackageCache.get_latest_for_community(community)

        if not cache:
            return Response({"error": "No cache available"}, status=503)

        last_modified = int(cache.created_at.timestamp())
        response = get_conditional_response(request, last_modified=last_modified)

        if response is None:
            url = request.build_absolute_uri(cache.index.data_url)
            url = replace_cdn(url, request.query_params.get("cdn"))
            response = redirect(url)

        response["Last-Modified"] = http_date(last_modified)
        response["Cache-Control"] = "public, max-age=0, s-maxage=300"
        return response
