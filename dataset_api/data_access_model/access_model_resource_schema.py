import graphene
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output

from dataset_api.decorators import validate_token
from dataset_api.models import Dataset, Resource
from dataset_api.data_access_model.models import DataAccessModel, DatasetAccessModelMap, AccessModelResource


class AccessModelResourceType(DjangoObjectType):
    class Meta:
        model = AccessModelResource
        fields = "__all__"


class DatasetAccessModelMapType(DjangoObjectType):
    class Meta:
        model = DatasetAccessModelMap
        fields = "__all__"


class ResourceFieldInput(graphene.InputObjectType):
    resource_id = graphene.ID(required=True)
    fields = graphene.List(of_type=graphene.String, required=True)


class AccessModelResourceInput(graphene.InputObjectType):
    id = graphene.ID()
    resource_map = graphene.List(of_type=ResourceFieldInput, required=True)
    access_model_id = graphene.ID(required=True)
    dataset_id = graphene.ID(required=True)


class Query(graphene.ObjectType):
    dataset_access_model = graphene.List(DatasetAccessModelMapType, dataset_id=graphene.ID())
    dataset_access_model_by_id = graphene.Field(DatasetAccessModelMapType, dataset_access_model_id=graphene.ID())

    @validate_token
    def resolve_dataset_access_model(self, info, dataset_id, **kwargs):
        try:
            dataset = Dataset.objects.get(id=dataset_id)
        except Dataset.DoesNotExist as e:
            return {"success": False,
                    "errors": {"organization_id": [{"message": "Dataset with id not found", "code": "404"}]}}
        return DatasetAccessModelMap.objects.all(dataset=dataset)

    @validate_token
    def resolve_dataset_access_model_by_id(self, info, dataset_access_model_id):
        return DatasetAccessModelMap.objects.get(pk=dataset_access_model_id)


class CreateAccessModelResource(Output, graphene.Mutation):
    class Arguments:
        access_model_resource_data = AccessModelResourceInput()

    access_model_resource = graphene.Field(AccessModelResourceType)

    @staticmethod
    def mutate(root, info, access_model_resource_data: AccessModelResourceInput):
        try:
            data_access_instance = DataAccessModel.objects.get(id=access_model_resource_data.access_model_id)
            dataset_instance = Dataset.objects.get(id=access_model_resource_data.dataset_id)

            dataset_access_map_instance = DatasetAccessModelMap(
                data_access_model=data_access_instance,
                dataset=dataset_instance
            )
            dataset_access_map_instance.save()

            for resources in access_model_resource_data.resource_map:
                try:
                    Resource.objects.get(id=resources.resource_id)
                    access_model_resource_instance = AccessModelResource(
                        resource_id=resources.resource_id,
                        fields=resources.resource_map,
                        dataset_access_map=dataset_access_map_instance
                    )
                    access_model_resource_instance.save()
                    return CreateAccessModelResource(access_model_resource=access_model_resource_instance)
                except Resource.DoesNotExist as e:
                    dataset_access_map_instance.delete()
                    return {"success": False, "errors": {"id": [{"message": "Resource id not found", "code": "404"}]}}
        except Dataset.DoesNotExist as e:
            return {"success": False, "errors": {"id": [{"message": "Dataset id not found", "code": "404"}]}}
        except DataAccessModel.DoesNotExist as e:
            return {"success": False, "errors": {"id": [{"message": "Access Model id not found", "code": "404"}]}}


class Mutation(graphene.ObjectType):
    access_model_resource = CreateAccessModelResource.Field()
