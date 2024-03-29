from typing import Iterable

import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output
from graphql import GraphQLError

from activity_log.signal import activity
from ..decorators import validate_token
from ..models.DataAccessModel import DataAccessModel
from dataset_api.enums import SubscriptionUnits, ValidationUnits, DataAccessModelStatus
from dataset_api.models import Organization, Agreement, Dataset, Policy
from ..models.LicenseAddition import LicenseAddition
from ..models.License import License
from .contract import create_contract
from .decorators import auth_user_action_dam, auth_query_dam
from ..utils import get_client_ip, log_activity

class DataAccessModelType(DjangoObjectType):
    active_users = graphene.Int()
    dataset_count = graphene.Int()

    class Meta:
        model = DataAccessModel
        fields = "__all__"

    def resolve_active_users(self: DataAccessModel, info):
        return Agreement.objects.filter(dataset_access_model__data_access_model=self).count()

    def resolve_dataset_count(self: DataAccessModel, info):
        return Dataset.objects.filter(datasetaccessmodel__data_access_model=self).count()


class Query(graphene.ObjectType):
    all_data_access_models = graphene.List(DataAccessModelType)
    org_data_access_models = graphene.List(
        DataAccessModelType, organization_id=graphene.ID()
    )
    data_access_model = graphene.Field(
        DataAccessModelType, data_access_model_id=graphene.ID()
    )

    @validate_token
    def resolve_all_data_access_models(self, info, username, **kwargs):
        return DataAccessModel.objects.all().order_by("-modified")

    @auth_query_dam(action="query||id")
    # Access : PMU/DPA of that org.
    def resolve_org_data_access_models(self, info, organization_id, role):
        if role == "PMU" or role == "DPA" or role == "DP":
            organization = Organization.objects.get(pk=organization_id)
            return DataAccessModel.objects.filter(Q(organization=organization) | Q(is_global=True)).order_by(
                "-modified"
            )
        else:
            raise GraphQLError("Access Denied")

    # Access : PMU/DPA of that org.
    @auth_query_dam(action="query||dam")
    def resolve_data_access_model(self, info, data_access_model_id, role):
        if role == "PMU" or role == "DPA":
            return DataAccessModel.objects.get(pk=data_access_model_id)
        else:
            raise GraphQLError("Access Denied")


class AccessTypes(graphene.Enum):
    OPEN = "OPEN"
    RESTRICTED = "RESTRICTED"
    REGISTERED = "REGISTERED"


class RateLimitUnits(graphene.Enum):
    SECOND = "SECOND"
    MINUTE = "MINUTE"
    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    YEAR = "YEAR"


class DataAccessModelInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=True)
    type = AccessTypes(required=True)
    description = graphene.String(required=True)
    contract = Upload(required=False)
    license = graphene.ID(required=True)
    #policy = graphene.ID(required=False)
    subscription_quota = graphene.Int(required=False)
    subscription_quota_unit = graphene.Enum.from_enum(SubscriptionUnits)(required=False)
    rate_limit = graphene.Int(required=True)
    rate_limit_unit = RateLimitUnits(required=True)
    additions: Iterable = graphene.List(of_type=graphene.ID, required=False, default=[])
    validation = graphene.Int(required=False)
    validation_unit = graphene.Enum.from_enum(ValidationUnits)(required=False)
    is_global = graphene.Boolean(required=False, default=False)


class DeleteDataAccessModelInput(graphene.InputObjectType):
    id = graphene.ID(required=True)


class DisableDataAccessModelInput(graphene.InputObjectType):
    id = graphene.ID(required=True)


class InvalidAddition(Exception):
    def __init__(self, addition_id):
        self.addition_id = addition_id
        super().__init__(f"License Addition with given {addition_id} not found")


def _add_update_license_additions(
        data_access_model_instance, dam_license: License, additions
):
    if not additions:
        return
    possible_additions = LicenseAddition.objects.filter(
        Q(license=dam_license) | Q(generic_item=True)
    )
    license_additions = [int(addition.id) for addition in possible_additions]
    data_access_model_instance.license_additions.clear()
    additions = [int(addition) for addition in additions]
    for addition_id in additions:
        if addition_id in license_additions:
            dam_addition = LicenseAddition.objects.get(id=addition_id)
            data_access_model_instance.license_additions.add(dam_addition)
        else:
            raise InvalidAddition(addition_id)
    data_access_model_instance.save()


class CreateDataAccessModel(Output, graphene.Mutation):
    class Arguments:
        data_access_model_data = DataAccessModelInput()

    data_access_model = graphene.Field(DataAccessModelType)

    @staticmethod
    @validate_token
    @auth_user_action_dam(action="create_dam")
    def mutate(root, info, username, data_access_model_data: DataAccessModelInput):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        if org_id:
            org_instance = Organization.objects.get(id=org_id)
        else:
            org_instance = None
        try:
            dam_license = License.objects.get(id=data_access_model_data.license)
        except License.DoesNotExist:
            raise GraphQLError("License with given id does not exist.")
        #if data_access_model_data.policy:
        #    policy_obj = Policy.objects.get(pk=data_access_model_data.policy)
        dam_obj = DataAccessModel.objects.filter(title__exact=data_access_model_data.title,
                                                 organization=org_instance)
        if len(dam_obj) >= 1:
            raise GraphQLError(
                "Access Model with the same title exists already. Please enter a unique title."
            )
        data_access_model_instance = DataAccessModel(
            title=data_access_model_data.title,
            type=data_access_model_data.type,
            description=data_access_model_data.description,
            organization=org_instance,
            contract=data_access_model_data.contract,
            license=dam_license,
            #policy=policy_obj if policy_obj else None,
            subscription_quota=data_access_model_data.subscription_quota,
            subscription_quota_unit=data_access_model_data.subscription_quota_unit,
            rate_limit=data_access_model_data.rate_limit,
            rate_limit_unit=data_access_model_data.rate_limit_unit,
            validation=data_access_model_data.validation,
            validation_unit=data_access_model_data.validation_unit,
            is_global=data_access_model_data.is_global if data_access_model_data.is_global else False,
        )
        data_access_model_instance.save()

        log_activity(
            target_obj=data_access_model_instance,
            ip=get_client_ip(info),
            target_group=org_instance,
            username=username,
            verb="Created",
        )
        try:
            _add_update_license_additions(
                data_access_model_instance,
                dam_license,
                data_access_model_data.additions,
            )
        except InvalidAddition as e:
            return {"success": False, "errors": {"id": [{str(e)}]}}
        
        #NOTE: Temporary fix for DAM creation/updation in PMU.
        if not data_access_model_data.is_global:
            create_contract(
                dam_license,
                data_access_model_data.additions,
                data_access_model_instance,
            )
        return CreateDataAccessModel(data_access_model=data_access_model_instance)


class UpdateDataAccessModel(Output, graphene.Mutation):
    class Arguments:
        data_access_model_data = DataAccessModelInput()

    data_access_model = graphene.Field(DataAccessModelType)

    @staticmethod
    @validate_token
    @auth_user_action_dam(action="update_dam")
    def mutate(root, info, username, data_access_model_data: DataAccessModelInput):
        org_id = info.context.META.get("HTTP_ORGANIZATION")
        if not data_access_model_data.id:
            return {
                "success": False,
                "errors": {
                    "id": [{"message": "Data Access Model id not found", "code": "404"}]
                },
            }

        try:
            data_access_model_instance = DataAccessModel.objects.get(
                id=data_access_model_data.id
            )
            if org_id:
                org_instance = Organization.objects.get(id=org_id)
            else:
                org_instance = None
            dam_license = License.objects.get(id=data_access_model_data.license)
        except (
                DataAccessModel.DoesNotExist,
                Organization.DoesNotExist,
                License.DoesNotExist,
        ) as e:
            return {
                "success": False,
                "errors": {"id": [{"message": str(e), "code": "404"}]},
            }
        
        #if data_access_model_data.policy:
        #    policy_obj = Policy.objects.get(pk=data_access_model_data.policy)

        dam_obj = DataAccessModel.objects.filter(title__exact=data_access_model_data.title,
                                                 organization=org_instance).exclude(id=data_access_model_instance.id)
        if len(dam_obj) >= 1:
            raise GraphQLError(
                "Access Model with the same title exists already. Please enter a unique title."
            )
        data_access_model_instance.title = data_access_model_data.title
        data_access_model_instance.type = data_access_model_data.type
        data_access_model_instance.description = data_access_model_data.description
        data_access_model_instance.organization = org_instance
        data_access_model_instance.contract = data_access_model_data.contract
        data_access_model_instance.license = dam_license
        #data_access_model_instance.policy=policy_obj if policy_obj else None
        data_access_model_instance.subscription_quota = data_access_model_data.subscription_quota
        data_access_model_instance.subscription_quota_unit = data_access_model_data.subscription_quota_unit
        data_access_model_instance.rate_limit = data_access_model_data.rate_limit
        data_access_model_instance.rate_limit_unit = data_access_model_data.rate_limit_unit
        data_access_model_instance.validation = data_access_model_data.validation
        data_access_model_instance.validation_unit = data_access_model_data.validation_unit
        data_access_model_instance.save()

        try:
            _add_update_license_additions(
                data_access_model_instance,
                dam_license,
                data_access_model_data.additions,
            )
        except InvalidAddition as e:
            return {"success": False, "errors": {"id": [{str(e)}]}}
        
        #NOTE: Temporary fix for DAM creation/updation in PMU.
        create_contract(
            dam_license,
            data_access_model_data.additions,
            data_access_model_instance,
        )

        log_activity(
            target_obj=data_access_model_instance,
            ip=get_client_ip(info),
            target_group=org_instance,
            username=username,
            verb="Updated",
        )
        return UpdateDataAccessModel(data_access_model=data_access_model_instance)


class DeleteDataAccessModel(Output, graphene.Mutation):
    class Arguments:
        data_access_model_data = DeleteDataAccessModelInput()

    success = graphene.String()

    # resource = graphene.Field(ResourceType)

    @staticmethod
    @validate_token
    @auth_user_action_dam(action="delete_dam")
    def mutate(
            root, info, data_access_model_data: DeleteDataAccessModelInput, username=""
    ):
        dam_instance = DataAccessModel.objects.get(id=data_access_model_data.id)
        log_activity(
            target_obj=dam_instance,
            ip=get_client_ip(info),
            target_group=dam_instance.organization,
            username=username,
            verb="Deleted",
        )
        dam_instance.delete()
        return DeleteDataAccessModel(success=True)


class DisableDataAccessModel(Output, graphene.Mutation):
    class Arguments:
        data_access_model_data = DisableDataAccessModelInput()

    success = graphene.String()

    data_access_model = graphene.Field(DataAccessModelType)

    @staticmethod
    @validate_token
    @auth_user_action_dam(action="delete_dam")
    def mutate(
            root, info, data_access_model_data: DeleteDataAccessModelInput, username=""
    ):
        dam_instance = DataAccessModel.objects.get(id=data_access_model_data.id)
        log_activity(
            target_obj=dam_instance,
            ip=get_client_ip(info),
            target_group=dam_instance.organization,
            username=username,
            verb="Disabled",
        )
        dam_instance.status = DataAccessModelStatus.DISABLED
        dam_instance.save()
        return DisableDataAccessModel(data_access_model=dam_instance)


class Mutation(graphene.ObjectType):
    create_data_access_model = CreateDataAccessModel.Field()
    update_data_access_model = UpdateDataAccessModel.Field()
    delete_data_access_model = DeleteDataAccessModel.Field()
    disable_data_access_model = DisableDataAccessModel.Field()
