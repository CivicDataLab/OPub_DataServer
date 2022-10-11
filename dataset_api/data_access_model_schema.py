import graphene
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload

from .models import DataAccessModel, Dataset, Resource, AccessModelResource
from .search import update_rating


class DataAccessModelType(DjangoObjectType):
    class Meta:
        model = DataAccessModel
        fields = "__all__"

class AccessModelResourceType(DjangoObjectType):
    class Meta:
        model = AccessModelResource
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
    dataset = graphene.String(required=True)
    contract_url = graphene.String(required=False)
    contract = Upload(required=False)
    license = graphene.String(required=True)
    quota_limit = graphene.Int(required=True)
    quota_limit_unit = QuotaUnits(required=True)
    rate_limit = graphene.Int(required=True)
    rate_limit_unit = RateLimitUnits(required=True)
    resources = graphene.List(of_type=graphene.String, required=True)

class AccessModelResourceInput(graphene.InputObjectType):
    resource_id = graphene.ID(required=True)
    fields = graphene.List(of_type=graphene.String, required=True)
    access_model_id = graphene.ID(required=True)

class CreateDataAccessModel(graphene.Mutation):
    class Arguments:
        data_access_model_data = DataAccessModelInput()

    data_access_model = graphene.Field(DataAccessModelType)
    # TODO: Reject if no resources passed
    @staticmethod
    def mutate(root, info, data_access_model_data: DataAccessModelInput):
        dataset = Dataset.objects.get(id=data_access_model_data.dataset)
        data_access_model_instance = DataAccessModel(
            title=data_access_model_data.title,
            type=data_access_model_data.type,
            description=data_access_model_data.description,
            dataset=dataset,
            contract_url=data_access_model_data.contract_url,
            contract=data_access_model_data.contract,
            license=data_access_model_data.license,
            quota_limit=data_access_model_data.quota_limit,
            quota_limit_unit=data_access_model_data.quota_limit_unit,
            rate_limit=data_access_model_data.rate_limit,
            rate_limit_unit=data_access_model_data.rate_limit_unit,
        )

        data_access_model_instance.save()
        for resource_id in data_access_model_data.resources:
            try:
                resource = Resource.objects.get(id=int(resource_id))
                data_access_model_instance.resources.add(resource)
            except Resource.DoesNotExist as e:
                pass
        data_access_model_instance.save()
        # Update rating in elasticsearch
        # update_rating(data_access_model_instance)
        return CreateDataAccessModel(data_access_model=data_access_model_instance)

class CreateAccessModelResource(graphene.Mutation):
    class Arguments:
        access_model_resource_data = AccessModelResourceInput()

    access_model_resource = graphene.Field(AccessModelResourceType)
    
    @staticmethod
    def mutate(root, info, access_model_resource_data: AccessModelResourceInput):
        try:
            data_access_instance = DataAccessModel.objects.get(id=access_model_resource_data.access_model_id)
            resource_instance = Resource.objects.get(id=access_model_resource_data.resource_id)
        except (Resource.DoesNotExist, DataAccessModel.DoesNotExist) as e:
            pass
        access_model_resource_instance = AccessModelResource(
            resource_id = resource_instance.id,
            fields = access_model_resource_data.fields,
            data_access_model_id = data_access_instance
        )
        
        access_model_resource_instance.save()
        return CreateAccessModelResource(access_model_resource=access_model_resource_instance)