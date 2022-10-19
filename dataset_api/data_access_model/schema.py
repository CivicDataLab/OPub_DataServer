import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output

from dataset_api.data_access_model.models import DataAccessModel
from dataset_api.enums import SubscriptionUnits
from dataset_api.models import Organization
from ..license.models import License, LicenseAddition
from .contract import create_contract
from .decorator import auth_user_action_dam


class DataAccessModelType(DjangoObjectType):
    class Meta:
        model = DataAccessModel
        fields = "__all__"


class Query(graphene.ObjectType):
    all_data_access_models = graphene.List(DataAccessModelType)
    org_data_access_models = graphene.List(DataAccessModelType, organization_id=graphene.ID())
    data_access_model = graphene.Field(DataAccessModelType, data_access_model_id=graphene.ID())

    def resolve_all_data_access_models(self, info, **kwargs):
        return DataAccessModel.objects.all().order_by("-modified")

    def resolve_org_data_access_models(self, info, organization_id):
        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            return {"success": False,
                    "errors": {"organization_id": [{"message": "Organization id not found", "code": "404"}]}}
        return DataAccessModel.objects.filter(organization=organization).order_by("-modified")

    def resolve_data_access_model(self, info, data_access_model_id):
        return DataAccessModel.objects.get(pk=data_access_model_id)


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
    organization = graphene.ID(required=True)
    contract = Upload(required=False)
    license = graphene.ID(required=True)
    subscription_quota = graphene.Int(required=True)
    subscription_quota_unit = graphene.Enum.from_enum(SubscriptionUnits)(required=True)
    rate_limit = graphene.Int(required=True)
    rate_limit_unit = RateLimitUnits(required=True)
    additions = graphene.List(of_type=graphene.ID, required=False, default=[])


class DeleteDataAccessModelInput(graphene.InputObjectType):
    id = graphene.ID(required=True)


class InvalidAddition(Exception):
    def __init__(self, addition_id):
        self.addition_id = addition_id
        super().__init__(f"License Addition with given {addition_id} not found")


def _add_update_license_additions(data_access_model_instance, dam_license: License, additions):
    possible_additions = LicenseAddition.objects.filter(Q(license=dam_license) | Q(generic_item=True))
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
    @auth_user_action_dam(action="create_dam")
    def mutate(root, info, data_access_model_data: DataAccessModelInput):
        org_instance = Organization.objects.get(id=data_access_model_data.organization)
        dam_license = License.objects.get(id=data_access_model_data.license)
        data_access_model_instance = DataAccessModel(
            title=data_access_model_data.title,
            type=data_access_model_data.type,
            description=data_access_model_data.description,
            organization=org_instance,
            contract=data_access_model_data.contract,
            license=dam_license,
            subscription_quota=data_access_model_data.subscription_quota,
            subscription_quota_unit=data_access_model_data.subscription_quota_unit,
            rate_limit=data_access_model_data.rate_limit,
            rate_limit_unit=data_access_model_data.rate_limit_unit,
        )

        data_access_model_instance.save()
        try:
            _add_update_license_additions(data_access_model_instance, dam_license, data_access_model_data.additions)
            create_contract(dam_license, data_access_model_data.additions, data_access_model_instance)
        except InvalidAddition as e:
            return {"success": False, "errors": {"id": [{str(e)}]}}

        return CreateDataAccessModel(data_access_model=data_access_model_instance)


class UpdateDataAccessModel(Output, graphene.Mutation):
    class Arguments:
        data_access_model_data = DataAccessModelInput()

    data_access_model = graphene.Field(DataAccessModelType)

    @staticmethod
    @auth_user_action_dam(action="update_dam")
    def mutate(root, info, data_access_model_data: DataAccessModelInput):
        if not data_access_model_data.id:
            return {"success": False,
                    "errors": {"id": [{"message": "Data Access Model id not found", "code": "404"}]}}

        try:
            data_access_model_instance = DataAccessModel.objects.get(id=data_access_model_data.id)
            org_instance = Organization.objects.get(id=data_access_model_data.organization)
            dam_license = License.objects.get(id=data_access_model_data.license)
        except (DataAccessModel.DoesNotExist, Organization.DoesNotExist, License.DoesNotExist) as e:
            return {"success": False,
                    "errors": {"id": [{"message": str(e), "code": "404"}]}}

        data_access_model_instance.title = data_access_model_data.title
        data_access_model_instance.type = data_access_model_data.type
        data_access_model_instance.description = data_access_model_data.description
        data_access_model_instance.organization = org_instance
        data_access_model_instance.contract = data_access_model_data.contract
        data_access_model_instance.license = dam_license
        data_access_model_instance.subscription_quota = data_access_model_data.subscription_quota
        data_access_model_instance.subscription_quota_unit = data_access_model_data.subscription_quota_unit
        data_access_model_instance.rate_limit = data_access_model_data.rate_limit
        data_access_model_instance.rate_limit_unit = data_access_model_data.rate_limit_unit
        data_access_model_instance.save()

        try:
            _add_update_license_additions(data_access_model_instance, dam_license, data_access_model_data.additions)
            create_contract(dam_license, data_access_model_data.additions, data_access_model_instance)
        except InvalidAddition as e:
            return {"success": False, "errors": {"id": [{str(e)}]}}

        return UpdateDataAccessModel(data_access_model=data_access_model_instance)


class DeleteDataAccessModel(Output, graphene.Mutation):
    class Arguments:
        data_access_model_data = DeleteDataAccessModelInput()

    success = graphene.String()

    # resource = graphene.Field(ResourceType)

    @staticmethod
    @auth_user_action_dam(action="delete_dam")
    def mutate(root, info, data_access_model_data: DeleteDataAccessModelInput):
        dam_instance = DataAccessModel.objects.get(id=data_access_model_data.id)
        dam_instance.delete()
        return DeleteDataAccessModel(success=True)


class Mutation(graphene.ObjectType):
    create_data_access_model = CreateDataAccessModel.Field()
    update_data_access_model = UpdateDataAccessModel.Field()
    delete_data_access_model = DeleteDataAccessModel.Field()
