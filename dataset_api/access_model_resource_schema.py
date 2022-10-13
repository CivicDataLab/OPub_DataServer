import graphene
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload

from .models import DataAccessModel, Dataset, Organization, Resource, AccessModelResource, DatasetAccessModelMap

class AccessModelResourceType(DjangoObjectType):
    class Meta:
        model = AccessModelResource
        fields = "__all__"

class ResourceFieldInput(graphene.InputObjectType):
    resource_id = graphene.ID(required=True)
    name = graphene.List(of_type=graphene.String, required=True)

class AccessModelResourceInput(graphene.InputObjectType):
    id = graphene.ID()
    fields = graphene.List(of_type=ResourceFieldInput, required=True)
    access_model_id = graphene.ID(required=True)
    dataset_id = graphene.ID(required=True)

class CreateAccessModelResource(graphene.Mutation):
    class Arguments:
        access_model_resource_data = AccessModelResourceInput()

    access_model_resource = graphene.Field(AccessModelResourceType)
    
    @staticmethod
    def mutate(root, info, access_model_resource_data: AccessModelResourceInput):
        try:
            data_access_instance = DataAccessModel.objects.get(id=int(access_model_resource_data.access_model_id))
            dataset_instance = Dataset.objects.get(id=int(access_model_resource_data.dataset_id))
            
            dataset_access_map_instance = DatasetAccessModelMap(
                data_access_model = data_access_instance,
                dataset = dataset_instance
            )
            dataset_access_map_instance.save()
            
            for field in access_model_resource_data.fields:
                try:
                    if field.resource_id:
                        resource_instance = Resource.objects.get(id=int(field.resource_id))
                        access_model_resource_instance = AccessModelResource(
                            resource_id = int(field.resource_id),
                            fields = field.name,
                            dataset_access_map = dataset_access_map_instance
                        )
                        access_model_resource_instance.save()
                except Resource.DoesNotExist as e:
                    return {"success": False, "errors": {"id": [{"message": "Resource id not found", "code": "404"}]}}
        except Dataset.DoesNotExist as e:
            return {"success": False, "errors": {"id": [{"message": "Dataset id not found", "code": "404"}]}}
        except DataAccessModel.DoesNotExist as e:
            return {"success": False, "errors": {"id": [{"message": "Access Model id not found", "code": "404"}]}}
        
        access_model_resource_instance.save()
        return CreateAccessModelResource(access_model_resource=access_model_resource_instance)