import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output
from graphql import GraphQLError

from dataset_api.models.Policy import Policy
from dataset_api.models import DataAccessModel, Organization
from .enums import PolicyStatus
from dataset_api.utils import get_client_ip, log_activity
from dataset_api.decorators import validate_token

class PolicyType(DjangoObjectType):
    class Meta:
        model = Policy
        fields = "__all__"


class Query(graphene.ObjectType):
    all_policy = graphene.List(PolicyType)
    approved_policy = graphene.List(PolicyType)
    policy_by_dam = graphene.List(PolicyType, dam_id=graphene.Int())
    policy_by_id = graphene.Field(PolicyType, policy_id=graphene.Int())
    policy_by_org = graphene.List(PolicyType)
    
    def resolve_all_policy(self, info, **kwargs):
        return Policy.objects.all().order_by("-modified")

    def resolve_approved_policy(self, info, **kwargs):
        return Policy.objects.filter(status=PolicyStatus.PUBLISHED.value).order_by("-modified")

    def resolve_policy_by_dam(self, info, dam_id, **kwargs):
        dam_object = DataAccessModel.objects.get(id=dam_id)
        return Policy.objects.filter(Q(data_access_model=dam_object), Q(status=PolicyStatus.PUBLISHED.value)).order_by("-modified")

    def resolve_policy_by_id(self, info, policy_id):
        return Policy.objects.get(pk=policy_id)

    def resolve_policy_by_org(self, info, **kwargs):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        organization = Organization.objects.get(id=org_id)
        return Policy.objects.filter(data_access_model__organization=organization).order_by("-modified")


class PolicyApproveRejectInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    status = graphene.String(required=True)
    reject_reason = graphene.String(required=False)


class PolicyInput(graphene.InputObjectType):
    id = graphene.ID(required=False)
    dam_id = graphene.ID(required=False)
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    file = Upload(required=False)
    remote_url = graphene.String(required=False)


class CreatePolicy(graphene.Mutation, Output):
    class Arguments:
        policy_data = PolicyInput(required=True)

    policy = graphene.Field(PolicyType)

    @staticmethod
    @validate_token
    # @check_license_role
    def mutate(root, info, username, policy_data: PolicyInput = None):
        try:
            dam_obj = DataAccessModel.objects.get(pk=policy_data.dam_id)
        except DataAccessModel.DoesNotExist as e:
            raise GraphQLError("Data access model with given id does not exist.")
        policy_instance = Policy(
            title=policy_data.title,
            description=policy_data.description,
            data_access_model=dam_obj,
        )
        if policy_data.file:
            policy_instance.file = policy_data.file
        if policy_data.remote_url:
            policy_instance.remote_url = policy_data.remote_url
        # if role == "DPA":
        #     license_instance.status = LicenseStatus.CREATED.value
        #     org_id = info.context.META.get("HTTP_ORGANIZATION")
        #     organization = Organization.objects.get(id=org_id)
        #     license_instance.created_organization_id = org_id
        # if role == "PMU":
        #     license_instance.status = LicenseStatus.PUBLISHED.value
        policy_instance.status = PolicyStatus.REQUESTED.value
        policy_instance.save()
        
        log_activity(
            target_obj=policy_instance,
            ip=get_client_ip(info),
            target_group=dam_obj.organization,
            username=username,
            verb=policy_instance.status,
        )
        return CreatePolicy(policy=policy_instance)


class UpdatePolicy(graphene.Mutation, Output):
    class Arguments:
        policy_data = PolicyInput(required=True)

    policy = graphene.Field(PolicyType)

    @staticmethod
    @validate_token
    # @check_license_role
    def mutate(root, info, username, policy_data: PolicyInput = None):
        try:
            policy_instance = Policy.objects.get(pk=policy_data.id)
        except Policy.DoesNotExist as e:
            raise GraphQLError("Policy with given id does not exist.")

        policy_instance.title = policy_data.title
        policy_instance.description = policy_data.description
        
        if policy_data.file:
            policy_instance.file = policy_data.file
        if policy_data.remote_url:
            policy_instance.remote_url = policy_data.remote_url
        # if role == "DPA":
        #     policy_instance.status = LicenseStatus.CREATED.value
        # if role == "PMU":
        #     policy_instance.status = LicenseStatus.PUBLISHED.value
        policy_instance.save()
        
        log_activity(
            target_obj=policy_instance,
            ip=get_client_ip(info),
            target_group=policy_instance.data_access_model.organization,
            username=username,
            verb="Updated",
        )
        
        return UpdatePolicy(policy=policy_instance)


class ApproveRejectPolicy(graphene.Mutation, Output):
    class Arguments:
        policy_data = PolicyApproveRejectInput(required=True)

    policy = graphene.Field(PolicyType)

    @staticmethod
    @validate_token
    # @auth_user_by_org(action="approve_license")
    def mutate(root, info, username, policy_data: PolicyApproveRejectInput = None):
        try:
            policy_instance = Policy.objects.get(pk=policy_data.id)
        except Policy.DoesNotExist as e:
            raise GraphQLError("Policy with given id does not exist.")
        
        policy_instance.status = policy_data.status
        if policy_data.reject_reason:
            policy_instance.reject_reason = policy_data.reject_reason
        policy_instance.save()
        
        log_activity(
            target_obj=policy_instance,
            ip=get_client_ip(info),
            target_group=policy_instance.data_access_model.organization,
            username=username,
            verb=policy_instance.status,
        )
        
        return ApproveRejectPolicy(policy=policy_instance)


class DeletePolicy(graphene.Mutation, Output):
    class Arguments:
        policy_id = graphene.ID(required=True)

    success = graphene.String()

    # resource = graphene.Field(ResourceType)

    @staticmethod
    # @check_license_role
    def mutate(root, info, policy_id: graphene.ID):
        policy_instance = Policy.objects.get(id=policy_id)
        policy_instance.delete()
        return DeletePolicy(success=True)


class Mutation(graphene.ObjectType):
    create_policy = CreatePolicy.Field()
    update_policy = UpdatePolicy.Field()
    approve_reject_policy = ApproveRejectPolicy.Field()
    delete_policy = DeletePolicy.Field()
