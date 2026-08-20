from django.test import override_settings

from thunderstore.abyss.storage import get_abyss_storage


@override_settings(ABYSS_S3_SECURE_URLS=True)
def test_abyss_storage_secure_urls_enabled_uses_https():
    assert get_abyss_storage().url_protocol == "https:"


@override_settings(ABYSS_S3_SECURE_URLS=False)
def test_abyss_storage_secure_urls_disabled_uses_http():
    assert get_abyss_storage().url_protocol == "http:"
