import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql_auth.bases import Output

from .models import DataAccessModel, Organization, License, LicenseAddition


# from .search import update_rating


class DataAccessModelType(DjangoObjectType):
    class Meta:
        model = DataAccessModel
        fields = "__all__"


class Query(graphene.ObjectType):
    all_data_access_models = graphene.List(DataAccessModelType)
    dataset_data_access_models = graphene.List(DataAccessModelType, dataset_id=graphene.Int())
    data_access_model = graphene.Field(DataAccessModelType, data_access_model_id=graphene.Int())

    def resolve_all_data_access_models(self, info, **kwargs):
        return DataAccessModel.objects.all().order_by("-modified")

    def resolve_dataset_data_access_models(self, info, dataset_id):
        return DataAccessModel.objects.filter(dataset=dataset_id).order_by("-modified")

    def resolve_data_access_model(self, info, data_access_model_id):
        return DataAccessModel.objects.get(pk=data_access_model_id)


class AccessTypes(graphene.Enum):
    OPEN = "OPEN"
    RESTRICTED = "RESTRICTED"
    REGISTERED = "REGISTERED"


class QuotaUnits(graphene.Enum):
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


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
    organization = graphene.String(required=True)
    contract_url = graphene.String(required=False)
    contract = Upload(required=False)
    license = graphene.ID(required=True)
    quota_limit = graphene.Int(required=True)
    quota_limit_unit = QuotaUnits(required=True)
    rate_limit = graphene.Int(required=True)
    rate_limit_unit = RateLimitUnits(required=True)
    additions = graphene.List(of_type=graphene.ID, required=False, default=[])


class InvalidAddition(Exception):
    def __init__(self, addition_id):
        self.addition_id = addition_id
        super().__init__(f"License Addition with given {addition_id} not found")


def _add_update_license_additions(data_access_model_instance, dam_license: License, additions):
    possible_additions = LicenseAddition.objects.filter(Q(license=dam_license) | Q(generic_item=True))
    license_additions = [addition.id for addition in possible_additions]
    data_access_model_instance.license_additions.clear()
    for addition_id in additions:
        if addition_id in license_additions:
            dam_addition = LicenseAddition.objects.get(id=addition_id)
            data_access_model_instance.license_additions.add(dam_addition)
        else:
            raise InvalidAddition(addition_id)


class CreateDataAccessModel(Output, graphene.Mutation):
    class Arguments:
        data_access_model_data = DataAccessModelInput()

    data_access_model = graphene.Field(DataAccessModelType)

    # TODO: Reject if no resources passed
    @staticmethod
    def mutate(root, info, data_access_model_data: DataAccessModelInput):
        org_instance = Organization.objects.get(id=data_access_model_data.organization)
        license = License.objects.get(id=data_access_model_data.license)
        data_access_model_instance = DataAccessModel(
            title=data_access_model_data.title,
            type=data_access_model_data.type,
            description=data_access_model_data.description,
            organization=org_instance,
            contract_url=data_access_model_data.contract_url,
            contract=data_access_model_data.contract,
            license=license,
            quota_limit=data_access_model_data.quota_limit,
            quota_limit_unit=data_access_model_data.quota_limit_unit,
            rate_limit=data_access_model_data.rate_limit,
            rate_limit_unit=data_access_model_data.rate_limit_unit,
        )

        try:
            _add_update_license_additions(data_access_model_instance, license, data_access_model_data.additions)
        except InvalidAddition as e:
            return {"success": False, "errors": {"id": [{str(e)}]}}

        data_access_model_instance.save()

        return CreateDataAccessModel(data_access_model=data_access_model_instance)


class Mutation(graphene.ObjectType):
    create_data_access_model = CreateDataAccessModel.Field()
