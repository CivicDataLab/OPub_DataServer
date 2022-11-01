import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

from dataset_api.decorators import validate_token, update_user_role
from dataset_api.enums import OrganizationRequestStatusType
from dataset_api.models import Organization
from dataset_api.models import OrganizationRequest


class OrganizationRequestType(DjangoObjectType):
    class Meta:
        model = OrganizationRequest
        fields = "__all__"


class Query(graphene.ObjectType):
    all_organization_requests = graphene.List(OrganizationRequestType)
    organization_request = graphene.Field(OrganizationRequestType, organization_request_id=graphene.Int())
    organization_request_user = graphene.List(OrganizationRequestType)

    def resolve_all_organization_requests(self, info, **kwargs):
        return OrganizationRequest.objects.all().order_by("-modified")

    def resolve_organization_request(self, info, organization_request_id):
        return OrganizationRequest.objects.get(pk=organization_request_id)

    @validate_token
    def resolve_organization_request_user(self, info, username, **kwargs):
        return OrganizationRequest.objects.filter(user=username).order_by("-modified")


class OrganizationRequestInput(graphene.InputObjectType):
    id = graphene.ID()
    description = graphene.String(required=True)
    organization = graphene.ID(required=True)


class OrganizationRequestUpdateInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = graphene.Enum.from_enum(OrganizationRequestStatusType)(required=True)
    remark = graphene.String(required=False)


class OrganizationRequestMutation(graphene.Mutation, Output):
    class Arguments:
        organization_request = OrganizationRequestInput()

    organization_request = graphene.Field(OrganizationRequestType)

    @staticmethod
    @validate_token
    def mutate(root, info, organization_request: OrganizationRequestInput = None, username=""):
        try:
            organization = Organization.objects.get(id=organization_request.organization)
        except Organization.DoesNotExist as e:
            return {"success": False,
                    "errors": {"id": [{"message": "Organization with given id not found", "code": "404"}]}}
        organization_request_instance = OrganizationRequest(
            status=OrganizationRequestStatusType.REQUESTED.value,
            description=organization_request.description,
            user=username,
            organization=organization,
        )
        organization_request_instance.save()
        organization.save()
        return OrganizationRequestMutation(organization_request=organization_request_instance)


class ApproveRejectOrganizationRequest(graphene.Mutation, Output):
    class Arguments:
        organization_request = OrganizationRequestUpdateInput()

    organization_request = graphene.Field(OrganizationRequestType)

    @staticmethod
    @update_user_role
    def mutate(root, info, organization_request: OrganizationRequestUpdateInput = None):
        try:
            organization_request_instance = OrganizationRequest.objects.get(id=organization_request.id)
        except OrganizationRequest.DoesNotExist as e:
            return {"success": False,
                    "errors": {"id": [{"message": "Organization joining with given id not found", "code": "404"}]}}
        organization_request_instance.status = organization_request.status
        if organization_request.remark:
            organization_request_instance.remark = organization_request.remark
        organization_request_instance.save()
        return ApproveRejectOrganizationRequest(organization_request=organization_request_instance)


class Mutation(graphene.ObjectType):
    organization_request = OrganizationRequestMutation.Field()
    approve_reject_organization_request = ApproveRejectOrganizationRequest.Field()
