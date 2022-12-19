from typing import Iterable

import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output
from graphql import GraphQLError

from dataset_api.models import Organization
from dataset_api.models.LicenseAddition import LicenseAddition
from dataset_api.models.License import License
from dataset_api.decorators import auth_user_by_org
from .decorators import check_license_role, auth_query_license
from .enums import LicenseStatus
from ..license_addition.enums import LICENSEADDITIONSTATE
from ..license_addition.license_addition_schema import LicenceAdditionInputType, _create_update_license_additions, \
    LicenseAdditionType


class LicenseType(DjangoObjectType):
    additions = graphene.List(LicenseAdditionType)

    class Meta:
        model = License
        fields = "__all__"

    def resolve_additions(self, info):
        try:
            return LicenseAddition.objects.filter(
                Q(license=self) | Q(generic_item=True)
            )
        except LicenseAddition.DoesNotExist as e:
            return []


class Query(graphene.ObjectType):
    all_license = graphene.List(LicenseType)
    licenses = graphene.List(LicenseType)
    license_by_org = graphene.List(LicenseType)
    license = graphene.Field(LicenseType, license_id=graphene.Int())

    def resolve_all_license(self, info, **kwargs):
        return License.objects.all().order_by("-modified")

    def resolve_licenses(self, info, **kwargs):
        return License.objects.filter(status=LicenseStatus.PUBLISHED.value).order_by("-modified")

    def resolve_license_by_org(self, info, **kwargs):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        organization = Organization.objects.get(id=org_id)
        return License.objects.filter(Q(created_organization=organization) |
                                      Q(status=LicenseStatus.PUBLISHED.value)).order_by("-modified")

    def resolve_license(self, info, license_id):
        return License.objects.get(pk=license_id)


class LicenseApproveRejectInput(graphene.InputObjectType):
    ids: Iterable = graphene.List(graphene.ID, required=True)
    reject_reason = graphene.String(required=False)
    # TODO: Re-visit duplicate license status
    status = graphene.String(required=True)
    # status = graphene.Enum.from_enum(LicenseStatus)(required=True)


class LicenseInput(graphene.InputObjectType):
    id = graphene.ID(required=False)
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    file = Upload(required=False)
    remote_url = graphene.String(required=False)
    license_additions = graphene.List(LicenceAdditionInputType, required=False, default=[])


class CreateLicense(graphene.Mutation, Output):
    class Arguments:
        license_data = LicenseInput(required=True)

    license = graphene.Field(LicenseType)

    @staticmethod
    @check_license_role
    def mutate(root, info, role, license_data: LicenseInput = None):

        license_instance = License(
            title=license_data.title,
            description=license_data.description,
        )
        if license_data.file:
            license_instance.file = license_data.file
        if license_data.remote_url:
            license_instance.remote_url = license_data.remote_url
        if role == "DPA":
            license_instance.status = LicenseStatus.CREATED.value
            org_id = info.context.META.get("HTTP_ORGANIZATION")
            organization = Organization.objects.get(id=org_id)
            license_instance.created_organization_id = org_id
        if role == "PMU":
            license_instance.status = LicenseStatus.PUBLISHED.value

        license_instance.save()
        if license_data.license_additions:
            _create_update_license_additions(
                license_instance, license_data.license_additions
            )
        return CreateLicense(license=license_instance)


class UpdateLicense(graphene.Mutation, Output):
    class Arguments:
        license_data = LicenseInput(required=True)

    license = graphene.Field(LicenseType)

    @staticmethod
    @check_license_role
    def mutate(root, info, role, license_data: LicenseInput = None):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        try:
            license_instance = License.objects.get(id=license_data.id)
        except License.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {
                            "message": "License or organization with given id not found",
                            "code": "404",
                        }
                    ]
                },
            }
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist as e:
            organization = None

        license_instance.title = license_data.title
        license_instance.description = license_data.description
        if organization:
            license_instance.created_organization = organization
        if license_data.file:
            license_instance.file = license_data.file
        if license_data.remote_url:
            license_instance.remote_url = license_data.remote_url
        if role == "DPA":
            license_instance.status = LicenseStatus.CREATED.value
        if role == "PMU":
            license_instance.status = LicenseStatus.PUBLISHED.value
        license_instance.save()
        if license_data.license_additions:
            _create_update_license_additions(
                license_instance, license_data.license_additions
            )
        return UpdateLicense(license=license_instance)


class ApproveRejectLicense(graphene.Mutation, Output):
    class Arguments:
        license_data = LicenseApproveRejectInput(required=True)

    license_requests = graphene.List(LicenseType)

    @staticmethod
    @auth_user_by_org(action="approve_license")
    def mutate(root, info, license_data: LicenseApproveRejectInput = None):
        errors = []
        license_requests = []
        for license_id in license_data.ids:
            try:
                license_instance = License.objects.get(id=license_id)
            except License.DoesNotExist as e:
                return errors.append(
                    {"message": "License with given id not found", "code": "404"}
                )

            license_instance.status = license_data.status
            if license_data.reject_reason:
                license_instance.reject_reason = license_data.reject_reason
            if license_data.status == LicenseStatus.PUBLISHED.value:
                for addition in license_instance.licenseaddition_set.all():
                    addition.status = LICENSEADDITIONSTATE.PUBLISHED.value
                    addition.save()
            license_instance.save()
            license_requests.append(license_instance)
        if errors:
            return {"success": False, "errors": {"ids": errors}}

        return ApproveRejectLicense(license_requests=license_requests)


class DeleteLicense(graphene.Mutation, Output):
    class Arguments:
        license_id = graphene.ID(required=True)

    success = graphene.String()

    # resource = graphene.Field(ResourceType)

    @staticmethod
    @check_license_role
    def mutate(root, info, license_id: graphene.ID):
        license_instance = License.objects.get(id=license_id)
        license_instance.delete()
        return DeleteLicense(success=True)


class Mutation(graphene.ObjectType):
    create_license = CreateLicense.Field()
    update_license = UpdateLicense.Field()
    approve_reject_license = ApproveRejectLicense.Field()
    delete_license = DeleteLicense.Field()
