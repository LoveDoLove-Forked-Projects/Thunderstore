import pytest
from rest_framework.authtoken.models import Token

from thunderstore.account.forms import (
    CreateServiceAccountForm,
    CreateTokenForm,
    DeleteServiceAccountForm,
    EditServiceAccountForm,
    create_service_account_username,
)
from thunderstore.account.models import ServiceAccount
from thunderstore.core.factories import UserFactory
from thunderstore.repository.models import (
    UploaderIdentityMember,
    UploaderIdentityMemberRole,
)


@pytest.mark.django_db
def test_service_account_fixture(service_account):
    username = create_service_account_username(service_account.uuid.hex)
    assert username == service_account.user.username


@pytest.mark.django_db
def test_service_account_create(user, uploader_identity):
    UploaderIdentityMember.objects.create(
        user=user,
        identity=uploader_identity,
        role=UploaderIdentityMemberRole.owner,
    )
    form = CreateServiceAccountForm(
        user,
        data={"identity": uploader_identity, "nickname": "Nickname"},
    )
    assert form.is_valid() is True
    service_account = form.save()
    username = create_service_account_username(service_account.uuid.hex)
    assert username == service_account.user.username
    assert service_account.user.first_name == "Nickname"
    assert service_account.created_at is not None
    assert service_account.last_used is None
    assert (
        uploader_identity.members.filter(
            user=service_account.user,
            role=UploaderIdentityMemberRole.member,
        ).exists()
        is True
    )


@pytest.mark.django_db
def test_service_account_create_nickname_too_long(user, uploader_identity):
    UploaderIdentityMember.objects.create(
        user=user,
        identity=uploader_identity,
        role=UploaderIdentityMemberRole.owner,
    )
    form = CreateServiceAccountForm(
        user,
        data={"identity": uploader_identity, "nickname": "x" * 1000},
    )
    assert form.is_valid() is False
    assert len(form.errors["nickname"]) == 1
    assert (
        form.errors["nickname"][0]
        == "Ensure this value has at most 32 characters (it has 1000)."
    )


@pytest.mark.django_db
def test_service_account_create_not_member(user, uploader_identity):
    assert uploader_identity.members.filter(user=user).exists() is False
    form = CreateServiceAccountForm(
        user,
        data={"identity": uploader_identity, "nickname": "Nickname"},
    )
    assert form.is_valid() is False
    assert len(form.errors["identity"]) == 1
    assert (
        form.errors["identity"][0]
        == "Select a valid choice. That choice is not one of the available choices."
    )


@pytest.mark.django_db
def test_service_account_create_not_owner(user, uploader_identity):
    UploaderIdentityMember.objects.create(
        user=user,
        identity=uploader_identity,
        role=UploaderIdentityMemberRole.member,
    )
    form = CreateServiceAccountForm(
        user,
        data={"identity": uploader_identity, "nickname": "Nickname"},
    )
    assert form.is_valid() is False
    assert len(form.errors["identity"]) == 1
    assert form.errors["identity"][0] == "Must be an owner to create a service account"


@pytest.mark.django_db
def test_service_account_delete(django_user_model, service_account):
    member = service_account.owner.members.first()
    assert member.role == UploaderIdentityMemberRole.owner
    assert django_user_model.objects.filter(pk=service_account.user.pk).exists() is True
    form = DeleteServiceAccountForm(
        member.user,
        data={"service_account": service_account},
    )
    assert form.is_valid()
    form.save()
    assert ServiceAccount.objects.filter(pk=service_account.pk).exists() is False
    assert (
        django_user_model.objects.filter(pk=service_account.user.pk).exists() is False
    )


@pytest.mark.django_db
def test_service_account_delete_not_member(service_account):
    user = UserFactory.create()
    assert service_account.owner.members.filter(user=user).exists() is False
    form = DeleteServiceAccountForm(
        user,
        data={"service_account": service_account},
    )
    assert form.is_valid() is False
    assert len(form.errors["service_account"]) == 1
    assert (
        form.errors["service_account"][0]
        == "Select a valid choice. That choice is not one of the available choices."
    )


@pytest.mark.django_db
def test_service_account_delete_not_owner(service_account):
    user = UserFactory.create()
    UploaderIdentityMember.objects.create(
        user=user,
        identity=service_account.owner,
        role=UploaderIdentityMemberRole.member,
    )
    form = DeleteServiceAccountForm(
        user,
        data={"service_account": service_account},
    )
    assert form.is_valid() is False
    assert len(form.errors["service_account"]) == 1
    assert (
        form.errors["service_account"][0]
        == "Must be an owner to delete a service account"
    )


@pytest.mark.django_db
def test_service_account_edit_nickname(service_account):
    member = service_account.owner.members.first()
    assert member.role == UploaderIdentityMemberRole.owner
    form = EditServiceAccountForm(
        member.user,
        data={"service_account": service_account, "nickname": "New nickname"},
    )
    assert form.is_valid()

    service_account = form.save()
    assert service_account.user.first_name == "New nickname"
    assert service_account.nickname == "New nickname"

    service_account = ServiceAccount.objects.get(pk=service_account.pk)
    assert service_account.user.first_name == "New nickname"
    assert service_account.nickname == "New nickname"


@pytest.mark.django_db
def test_service_account_edit_nickname_too_long(service_account):
    member = service_account.owner.members.first()
    assert member.role == UploaderIdentityMemberRole.owner
    form = EditServiceAccountForm(
        member.user,
        data={"service_account": service_account, "nickname": "x" * 1000},
    )
    assert form.is_valid() is False
    assert len(form.errors["nickname"]) == 1
    assert (
        form.errors["nickname"][0]
        == "Ensure this value has at most 32 characters (it has 1000)."
    )


@pytest.mark.django_db
def test_service_account_edit_not_member(service_account):
    user = UserFactory.create()
    assert service_account.owner.members.filter(user=user).exists() is False
    form = EditServiceAccountForm(
        user,
        data={"service_account": service_account, "nickname": "New nickname"},
    )
    assert form.is_valid() is False
    assert len(form.errors["service_account"]) == 1
    assert (
        form.errors["service_account"][0]
        == "Select a valid choice. That choice is not one of the available choices."
    )


@pytest.mark.django_db
def test_service_account_edit_not_owner(service_account):
    user = UserFactory.create()
    UploaderIdentityMember.objects.create(
        user=user,
        identity=service_account.owner,
        role=UploaderIdentityMemberRole.member,
    )
    form = EditServiceAccountForm(
        user,
        data={"service_account": service_account, "nickname": "New nickname"},
    )
    assert form.is_valid() is False
    assert len(form.errors["service_account"]) == 1
    assert (
        form.errors["service_account"][0]
        == "Must be an owner to edit a service account"
    )


@pytest.mark.django_db
def test_service_account_create_token(service_account):
    member = service_account.owner.members.first()
    assert member.role == UploaderIdentityMemberRole.owner
    form = CreateTokenForm(
        member.user,
        data={"service_account": service_account},
    )
    assert form.is_valid()
    token = form.save()
    assert service_account.user == token.user


@pytest.mark.django_db
def test_service_account_create_token_not_member(service_account):
    user = UserFactory.create()
    assert service_account.owner.members.filter(user=user).exists() is False
    form = CreateTokenForm(
        user,
        data={"service_account": service_account},
    )
    assert form.is_valid() is False
    assert len(form.errors["service_account"]) == 1
    assert (
        form.errors["service_account"][0]
        == "Select a valid choice. That choice is not one of the available choices."
    )


@pytest.mark.django_db
def test_service_account_create_token_not_owner(service_account):
    user = UserFactory.create()
    UploaderIdentityMember.objects.create(
        user=user,
        identity=service_account.owner,
        role=UploaderIdentityMemberRole.member,
    )
    form = CreateTokenForm(
        user,
        data={"service_account": service_account},
    )
    assert form.is_valid() is False
    assert len(form.errors["service_account"]) == 1
    assert (
        form.errors["service_account"][0]
        == "Must be an owner to generate a service account token"
    )


@pytest.mark.django_db
def test_service_account_token_fixture(service_account_token):
    assert service_account_token.user.service_account


@pytest.mark.django_db
def test_service_account_token_last_used(
    api_client,
    service_account_token,
):
    original_created_at = service_account_token.user.service_account.created_at
    original_last_used = service_account_token.user.service_account.last_used
    api_client.credentials(HTTP_AUTHORIZATION="Bearer " + service_account_token.key)
    response = api_client.get(
        "/api/experimental/current-user/",
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    assert "capabilities" in response.content.decode()
    service_account_token = Token.objects.get(pk=service_account_token.pk)
    assert service_account_token.user.service_account.created_at == original_created_at
    assert service_account_token.user.service_account.last_used != original_last_used
