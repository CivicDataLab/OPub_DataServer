import graphene
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output
from graphql import GraphQLError
from django.db.models import Q

from activity_log.signal import activity
from .models import (
    Organization,
    OrganizationCreateRequest,
    Catalog,
    Resource,
    Dataset,
    Sector,
)
from .decorators import (
    validate_token,
    create_user_org,
    auth_user_by_org,
    auth_request_org,
)
from .enums import OrganizationTypes, OrganizationCreationStatusType
from .utils import get_client_ip


class CreateOrganizationType(DjangoObjectType):
    class Meta:
        model = OrganizationCreateRequest
        fields = "__all__"


class OrganizationType(DjangoObjectType):
    username = graphene.String()
    api_count = graphene.Int()
    dataset_count = graphene.Int()
    usecase_count = graphene.Int()

    class Meta:
        model = Organization
        fields = "__all__"

    @auth_request_org
    def resolve_username(self, info, username=""):
        return username

    def resolve_api_count(self, info):
        api = Resource.objects.filter(
            Q(dataset__dataset_type__exact="API"),
            Q(dataset__status__exact="PUBLISHED"),
            Q(dataset__catalog__organization=self.id),
        ).count()
        return api

    def resolve_dataset_count(self, info):
        dataset = Dataset.objects.filter(
            Q(status__exact="PUBLISHED"),
            Q(catalog__organization=self.id),
        ).count()
        return dataset

    def resolve_usecase_count(self, info):
        usecase = Sector.objects.filter(
            Q(dataset__catalog__organization=self.id),
            Q(dataset__status__exact="PUBLISHED"),
        )
        return len(set(usecase))


class Query(graphene.ObjectType):
    all_organizations = graphene.List(OrganizationType)
    organization_by_id = graphene.Field(
        OrganizationType, organization_id=graphene.Int()
    )
    organization_by_title = graphene.Field(
        OrganizationType, organization_title=graphene.String()
    )
    organizations = graphene.List(OrganizationType)

    requested_organizations = graphene.List(OrganizationType)

    # TODO: Allow all org list for PMU? Current State -- YES
    @auth_user_by_org(action="query")
    def resolve_all_organizations(self, info, role, **kwargs):
        if role == "PMU":
            return Organization.objects.all().order_by("-modified")
        else:
            raise GraphQLError("Access Denied")

    # Access : DPA of that org.
    @auth_user_by_org(action="query")
    def resolve_organization_by_id(self, info, role, organization_id):
        if role == "DPA" or role == "PMU":
            return Organization.objects.get(pk=organization_id)
        else:
            raise GraphQLError("Access Denied")

    # Access : All
    def resolve_organization_by_title(self, info, organization_title, **kwargs):
        return Organization.objects.get(
            Q(title__iexact=organization_title),
            Q(
                organizationcreaterequest__status=OrganizationCreationStatusType.APPROVED.value
            ),
        )

    # Access : All
    def resolve_organizations(self, info, **kwargs):
        return Organization.objects.filter(
            organizationcreaterequest__status=OrganizationCreationStatusType.APPROVED.value
        )

    # Access : PMU
    @auth_user_by_org(action="query")
    def resolve_requested_organizations(self, info, role, **kwargs):
        if role == "PMU":
            return Organization.objects.filter(
                organizationcreaterequest__status=OrganizationCreationStatusType.REQUESTED.value
            ).order_by("-modified")
        else:
            raise GraphQLError("Access Denied")


class OrganizationInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    logo = Upload(required=False, description="Logo for the Company.")
    homepage = graphene.String(required=False)
    contact = graphene.String(required=False)
    organization_types = graphene.Enum.from_enum(OrganizationTypes)(required=True)
    data_description = graphene.String(required=True)
    upload_sample_data_file = Upload(required=False)
    sample_data_url = graphene.String(required=False)


class OrganizationPatchInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=False)
    description = graphene.String(required=False)
    logo = Upload(required=False, description="Logo for the Company.")
    homepage = graphene.String(required=False)
    contact = graphene.String(required=False)


class ApproveRejectOrganizationApprovalInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = graphene.Enum.from_enum(OrganizationCreationStatusType)(required=True)
    remark = graphene.String(required=False)


class CreateOrganization(Output, graphene.Mutation):
    class Arguments:
        organization_data = OrganizationInput(required=True)

    organization = graphene.Field(CreateOrganizationType)

    @staticmethod
    @create_user_org
    def mutate(root, info, organization_data: OrganizationInput = None):
        organization_additional_info_instance = OrganizationCreateRequest(
            title=organization_data.title,
            description=organization_data.description,
            logo=organization_data.logo,
            contact_email=organization_data.contact,
            homepage=organization_data.homepage,
            organization_types=organization_data.organization_types,
            upload_sample_data_file=organization_data.upload_sample_data_file,
            data_description=organization_data.data_description,
            sample_data_url=organization_data.sample_data_url,
            status=OrganizationCreationStatusType.REQUESTED.value,
        )
        organization_additional_info_instance.save()
        return CreateOrganization(organization=organization_additional_info_instance)


class UpdateOrganization(Output, graphene.Mutation):
    class Arguments:
        organization_data = OrganizationInput(required=True)

    organization = graphene.Field(CreateOrganizationType)

    @staticmethod
    @auth_user_by_org(action="update_organization")
    def mutate(root, info, role, organization_data: OrganizationInput = None):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        org_id = organization_data.id if organization_data.id else org_id
        try:
            organization_create_request_instance = (
                OrganizationCreateRequest.objects.get(organization_ptr_id=org_id)
            )
        except OrganizationCreateRequest.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {
                            "message": "Organization with given id not found",
                            "code": "404",
                        }
                    ]
                },
            }
        organization_create_request_instance.title = organization_data.title
        organization_create_request_instance.description = organization_data.description
        organization_create_request_instance.logo = organization_data.logo
        organization_create_request_instance.contact_email = organization_data.contact
        organization_create_request_instance.homepage = organization_data.homepage
        organization_create_request_instance.organization_types = (
            organization_data.organization_types
        )
        organization_create_request_instance.data_description = (
            organization_data.data_description
        )
        organization_create_request_instance.sample_data_url = (
            organization_data.sample_data_url
        )
        organization_create_request_instance.upload_sample_data_file = (
            organization_data.upload_sample_data_file
        )
        organization_create_request_instance.save()
        return CreateOrganization(organization=organization_create_request_instance)


class ApproveRejectOrganizationApproval(Output, graphene.Mutation):
    class Arguments:
        organization_data = ApproveRejectOrganizationApprovalInput(required=True)

    organization = graphene.Field(CreateOrganizationType)

    @staticmethod
    @validate_token
    @auth_user_by_org(action="approve_organization")
    def mutate(
        root,
        info,
        username="",
        organization_data: ApproveRejectOrganizationApprovalInput = None,
    ):
        try:
            organization_create_request_instance = (
                OrganizationCreateRequest.objects.get(
                    organization_ptr_id=organization_data.id
                )
            )
        except OrganizationCreateRequest.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {
                            "message": "Organization with given id not found",
                            "code": "404",
                        }
                    ]
                },
            }
        if organization_data.status == "REJECTED":
            organization_create_request_instance.status = (
                OrganizationCreationStatusType.REJECTED.value
            )
        else:
            organization_create_request_instance.status = (
                OrganizationCreationStatusType.APPROVED.value
            )
            organization = Organization.objects.get(pk=organization_data.id)
            # Create catalog if org is APPROVED.
            catalog_instance = Catalog(
                title=organization.title,
                description=organization.description,
                organization=organization,
            )
            catalog_instance.save()

        organization_create_request_instance.remark = organization_data.remark
        organization_create_request_instance.save()
        activity.send(
            username,
            verb=organization_data.status,
            target=organization_create_request_instance,
            target_group=organization_create_request_instance,
            ip=get_client_ip(info),
        )
        return ApproveRejectOrganizationApproval(
            organization=organization_create_request_instance
        )


class PatchOrganization(Output, graphene.Mutation):
    class Arguments:
        organization_data = OrganizationPatchInput(required=True)

    organization = graphene.Field(OrganizationType)

    @staticmethod
    @auth_user_by_org(action="update_organization")
    def mutate(root, info, organization_data: OrganizationPatchInput = None):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        org_id = organization_data.id if organization_data.id else org_id
        organization_instance = Organization.objects.get(id=org_id)

        if organization_data.title:
            organization_instance.title = organization_data.title
        if organization_data.description:
            organization_instance.description = organization_data.description
        if organization_data.contact:
            organization_instance.contact_email = organization_data.contact
        if organization_data.homepage:
            organization_instance.homepage = organization_data.homepage
        if organization_data.logo:
            organization_instance.logo = organization_data.logo
        organization_instance.save()

        return PatchOrganization(organization=organization_instance)


class Mutation(graphene.ObjectType):
    create_organization = CreateOrganization.Field()
    update_organization = UpdateOrganization.Field()
    patch_organization = PatchOrganization.Field()
    approve_reject_organization_approval = ApproveRejectOrganizationApproval.Field()
