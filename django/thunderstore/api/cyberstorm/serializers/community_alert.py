from rest_framework import serializers


class CyberstormCommunityAlertSerializer(serializers.Serializer):
    id = serializers.IntegerField()  # noqa: A003
    message = serializers.CharField()
    variant = serializers.CharField()
    datetime_created = serializers.DateTimeField()
    datetime_updated = serializers.DateTimeField()
