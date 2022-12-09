from typing import Iterable

import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from graphql_auth.bases import Output

from dataset_api.models import DataAccessModel, DataRequest, ResourceSchema
from dataset_api.models import Dataset, Resource, DatasetAccessModelRequest
from dataset_api.models import DatasetAccessModel
from dataset_api.models import DatasetAccessModelResource
from .decorators import auth_action_dam_resource
from ..enums import DataType


class AccessModelResourceType(DjangoObjectType):
    supported_formats = graphene.List(graphene.String)

    class Meta:
        model = DatasetAccessModelResource
        fields = "__all__"

    def resolve_supported_formats(self: DatasetAccessModelResource, info):
        resource = self.resource
        if resource.dataset.dataset_type == DataType.FILE.value:
            if resource.filedetails.format in ["CSV", "XML", "JSON"]:
                return ["CSV", "XML", "JSON"]
            else:
                return resource.filedetails.format
        elif resource.dataset.dataset_type == DataType.API.value:
            if resource.apidetails.supported_formats:
                return resource.apidetails.supported_formats
        return []


class DatasetAccessModelType(DjangoObjectType):
    resource_formats = graphene.List(of_type=graphene.String)
    usage = graphene.Int()

    class Meta:
        model = DatasetAccessModel
        fields = "__all__"

    def resolve_resource_formats(self: DatasetAccessModel, info):
        formats = []
        for dam_resource in self.datasetaccessmodelresource_set.all():
            has_resource = hasattr(dam_resource, "resource")
            if has_resource and hasattr(dam_resource.resource, "apidetails"):
                formats.append(dam_resource.resource.apidetails.response_type)
            if has_resource and hasattr(dam_resource.resource, "filedetails"):
                formats.append(dam_resource.resource.filedetails.format)
        return list(set(formats))

    def resolve_usage(self: DatasetAccessModel, info):
        try:
            dam_requests = DatasetAccessModelRequest.objects.filter(
                access_model_id=self.id
            )
            # dam_requests = self.datasetaccessmodelrequest_set.all()
            print(
                [
                    x.datarequest_set.filter(status="FETCHED").count()
                    for x in dam_requests
                ]
            )
            return sum(
                [
                    x.datarequest_set.filter(status="FETCHED").count()
                    for x in dam_requests
                ]
            )
        except (DatasetAccessModelRequest.DoesNotExist, DataRequest.DoesNotExist) as e:
            return 0


class ResourceFieldInput(graphene.InputObjectType):
    resource_id = graphene.ID(required=True)
    fields = graphene.List(of_type=graphene.String, required=True)


class AccessModelResourceInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=True)
    resource_map: Iterable = graphene.List(of_type=ResourceFieldInput, required=True)
    access_model_id = graphene.ID(required=True)
    dataset_id = graphene.ID(required=True)


class DeleteAccessModelResourceInput(graphene.InputObjectType):
    dataset_id = graphene.ID(required=True)


class CreateAccessModelResource(Output, graphene.Mutation):
    class Arguments:
        access_model_resource_data = AccessModelResourceInput()

    access_model_resource = graphene.Field(DatasetAccessModelType)

    @staticmethod
    @auth_action_dam_resource(action="create_dam_resource")
    def mutate(root, info, access_model_resource_data: AccessModelResourceInput):
        try:
            data_access_instance = DataAccessModel.objects.get(
                id=access_model_resource_data.access_model_id
            )
            dataset_instance = Dataset.objects.get(
                id=access_model_resource_data.dataset_id
            )

            dataset_access_model = DatasetAccessModel(
                data_access_model=data_access_instance, dataset=dataset_instance,
                title=access_model_resource_data.title,
            )
            dataset_access_model.save()

            if (
                    not access_model_resource_data.resource_map
                    or len(access_model_resource_data.resource_map) == 0
            ):
                raise GraphQLError(
                    "Please select at least one distribution and corresponding fields"
                )

            for resources in access_model_resource_data.resource_map:
                try:
                    resource = Resource.objects.get(id=resources.resource_id)
                    resource_schema = ResourceSchema.objects.filter(id__in=resources.fields).all()
                    access_model_resource_instance = DatasetAccessModelResource(
                        resource_id=resources.resource_id,
                        dataset_access_model=dataset_access_model,
                    )
                    access_model_resource_instance.save()
                    access_model_resource_instance.fields.set(resource_schema)
                except Resource.DoesNotExist as e:
                    dataset_access_model.delete()
                    return {
                        "success": False,
                        "errors": {
                            "id": [{"message": "Resource id not found", "code": "404"}]
                        },
                    }
                except ResourceSchema.DoesNotExist as e:
                    dataset_access_model.delete()
                    return {
                        "success": False,
                        "errors": {
                            "id": [{"message": "Field with this id not found", "code": "404"}]
                        },
                    }
            return CreateAccessModelResource(access_model_resource=dataset_access_model)
        except Dataset.DoesNotExist as e:
            return {
                "success": False,
                "errors": {"id": [{"message": "Dataset id not found", "code": "404"}]},
            }
        except DataAccessModel.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [{"message": "Access Model id not found", "code": "404"}]
                },
            }


class UpdateAccessModelResource(Output, graphene.Mutation):
    class Arguments:
        access_model_resource_data = AccessModelResourceInput()

    access_model_resource = graphene.Field(DatasetAccessModelType)

    @staticmethod
    # @auth_action_dam_resource(action="update_dam_resource")
    def mutate(root, info, access_model_resource_data: AccessModelResourceInput):
        try:
            dataset_access_model_instance = DatasetAccessModel.objects.get(
                pk=access_model_resource_data.id
            )
            if (
                    not access_model_resource_data.resource_map
                    or len(access_model_resource_data.resource_map) == 0
            ):
                raise GraphQLError(
                    "Please select at least one distribution and corresponding fields"
                )
            dataset_access_model_instance.title = access_model_resource_data.title
            dataset_access_model_instance.save()
            
            # Getting id's that were removed.
            get_all_resources = list(DatasetAccessModelResource.objects.filter(dataset_access_model_id=access_model_resource_data.id).values_list("resource_id", flat=True))
            # print("---------", get_all_resources, type(get_all_resources[0]))
            for resources in access_model_resource_data.resource_map:
                # print(resources.resource_id)
                try:
                    # print("removing value", type(resources.resource_id))
                    get_all_resources.remove(int(resources.resource_id))
                except Exception as e:
                    print(str(e))
            # Deleting removed resources.
            # print("bef del", get_all_resources)
            dam_resource_instance = DatasetAccessModelResource.objects.filter(resource_id__in=get_all_resources)
            # print("del obj", dam_resource_instance)
            if dam_resource_instance.exists():
                for resource in dam_resource_instance:
                    resource.delete()
            
            # Creating or Updating resources.
            for resources in access_model_resource_data.resource_map:
                resource_schema = ResourceSchema.objects.filter(id__in=resources.fields).all()
                try:
                    resource = Resource.objects.get(id=resources.resource_id)
                    access_model_resource_instance = (
                        DatasetAccessModelResource.objects.get(
                            dataset_access_model=dataset_access_model_instance,
                            resource_id=resources.resource_id,
                        )
                    )
                    access_model_resource_instance.fields.set(resource_schema)
                    access_model_resource_instance.save()
                except DatasetAccessModelResource.DoesNotExist as e:
                    try:
                        resource = Resource.objects.get(id=resources.resource_id)
                        access_model_resource_instance = DatasetAccessModelResource(
                            resource_id=resources.resource_id,
                            dataset_access_model=dataset_access_model_instance,
                        )
                        access_model_resource_instance.save()
                        access_model_resource_instance.fields.set(resource_schema)
                        access_model_resource_instance.save()
                    except Resource.DoesNotExist as e:
                        return {
                            "success": False,
                            "errors": {
                                "id": [
                                    {"message": "Resource id not found", "code": "404"}
                                ]
                            },
                        }
            return UpdateAccessModelResource(
                access_model_resource=dataset_access_model_instance
            )
        except DatasetAccessModel.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {
                            "message": "Dataset Access Model Map id not found",
                            "code": "404",
                        }
                    ]
                },
            }


class DeleteAccessModelResource(Output, graphene.Mutation):
    class Arguments:
        access_model_resource_data = DeleteAccessModelResourceInput()

    access_model_resource = graphene.Field(DatasetAccessModelType)

    @staticmethod
    @auth_action_dam_resource(action="delete_dam_resource")
    def mutate(root, info, access_model_resource_data: DeleteAccessModelResourceInput):
        try:
            access_model_map_instance = DatasetAccessModel.objects.get(
                pk=access_model_resource_data.dataset_id
            )
            access_model_resource_instance = DatasetAccessModelResource.objects.filter(
                id=access_model_resource_data.dataset_id
            )
            if access_model_resource_instance.exists():
                for resource in access_model_resource_instance:
                    resource.delete()
                access_model_map_instance.delete()
        except DatasetAccessModel.DoesNotExist as e:
            return {
                "success": False,
                "errors": {
                    "id": [
                        {
                            "message": "Dataset Access Model Map id not found",
                            "code": "404",
                        }
                    ]
                },
            }
        return DeleteAccessModelResource(success=True)


class Mutation(graphene.ObjectType):
    access_model_resource = CreateAccessModelResource.Field()
    update_access_model_resource = UpdateAccessModelResource.Field()
    delete_access_model_resource = DeleteAccessModelResource.Field()
