import graphene
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output

from .models import Organization, OrganizationCreateRequest
from .decorators import validate_token, create_user_org
from .enums import OrganizationTypes, OrganizationCreationStatusType


class CreateOrganizationType(DjangoObjectType):
    class Meta:
        model = OrganizationCreateRequest
        fields = "__all__"


class OrganizationType(DjangoObjectType):
    class Meta:
        model = Organization
        fields = "__all__"


class Query(graphene.ObjectType):
    all_organizations = graphene.List(OrganizationType)
    organization_by_id = graphene.Field(
        OrganizationType, organization_id=graphene.Int()
    )
    organization_by_title = graphene.Field(
        OrganizationType, organization_title=graphene.String()
    )
    organizations = graphene.List(OrganizationType)

    # TODO: Allow all org list for PMU?
    def resolve_all_organizations(self, info, **kwargs):
        return Organization.objects.all().order_by("-modified")

    def resolve_organization_by_id(self, info, organization_id):
        return Organization.objects.get(pk=organization_id)

    def resolve_organization_by_title(self, info, organization_title):
        return Organization.objects.get(title__iexact=organization_title)

    def resolve_organizations(self, info, **kwargs):
        return Organization.objects.filter(
            organizationcreaterequest__status=OrganizationCreationStatusType.APPROVED.value
        )


class OrganizationInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    logo = Upload(required=False, description="Logo for the Company.")
    homepage = graphene.String(required=False)
    contact = graphene.String(required=False)
    organization_types = graphene.Enum.from_enum(OrganizationTypes)(required=True)
    data_description = graphene.String(required=True)
    upload_sample_data_file = Upload(required=False)
    sample_data_url = graphene.String(required=False)


class ApproveRejectOrganizationApprovalInput(graphene.InputObjectType):
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
    @validate_token
    def mutate(root, info, organization_data: OrganizationInput = None):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        try:
            organization_create_request_instance = (
                OrganizationCreateRequest.objects.get(
                    organization_ptr_id=org_id
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
    def mutate(
            root, info, organization_data: ApproveRejectOrganizationApprovalInput = None
    ):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        try:
            organization_create_request_instance = (
                OrganizationCreateRequest.objects.get(
                    organization_ptr_id=org_id
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
        organization_create_request_instance.remark = organization_data.remark
        organization_create_request_instance.save()
        return ApproveRejectOrganizationApproval(
            organization=organization_create_request_instance
        )


class Mutation(graphene.ObjectType):
    create_organization = CreateOrganization.Field()
    update_organization = UpdateOrganization.Field()
    approve_reject_organization_approval = ApproveRejectOrganizationApproval.Field()
