from typing import Iterable

import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from graphql_auth.bases import Output

from dataset_api.models import DataAccessModel, ResourceSchema
from dataset_api.models import Dataset, Resource, Policy
from dataset_api.models import DatasetAccessModel
from dataset_api.models import DatasetAccessModelResource
from .decorators import auth_action_dam_resource
from ..dataset_access_model.enums import PAYMENTTYPES
from ..dataset_access_model.schema import DatasetAccessModelType
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
                return [resource.filedetails.format]
        elif resource.dataset.dataset_type == DataType.API.value:
            if resource.apidetails.supported_formats:
                return resource.apidetails.supported_formats
        return []


class ParameterKeyValueType(graphene.InputObjectType):
    key = graphene.String()
    value = graphene.String()


class ResourceFieldInput(graphene.InputObjectType):
    resource_id = graphene.ID(required=True)
    fields = graphene.List(of_type=graphene.String, required=True)
    sample_enabled = graphene.Boolean(required=False)
    sample_rows = graphene.Int(required=False)
    parameters = graphene.List(of_type=ParameterKeyValueType)


class AccessModelResourceInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(required=True)
    resource_map: Iterable = graphene.List(of_type=ResourceFieldInput, required=True)
    access_model_id = graphene.ID(required=True)
    dataset_id = graphene.ID(required=True)
    policy_id = graphene.ID(required=False)
    payment_type = graphene.Enum.from_enum(PAYMENTTYPES)(required=True)
    payment = graphene.Int(required=False)


class DeleteAccessModelResourceInput(graphene.InputObjectType):
    dataset_id = graphene.ID(required=True)
    dam_id = graphene.ID(required=True)


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
            policy_instance = Policy.objects.get(pk=access_model_resource_data.policy_id)
            dam_obj = DatasetAccessModel.objects.filter(title__exact=access_model_resource_data.title,
                                                        dataset__catalog__organization=dataset_instance.catalog.organization)
            if len(dam_obj) >= 1:
                raise GraphQLError(
                    "Dataset Access Model with Same name already exists"
                )
            dataset_access_model = DatasetAccessModel(
                data_access_model=data_access_instance, dataset=dataset_instance,
                title=access_model_resource_data.title, policy=policy_instance,
                payment_type=access_model_resource_data.payment_type
            )
            if access_model_resource_data.payment:
                dataset_access_model.payment = access_model_resource_data.payment

            dataset_access_model.save()

            if (
                    not access_model_resource_data.resource_map
                    or len(access_model_resource_data.resource_map) == 0
            ):
                dataset_access_model.delete()
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
                    if resources.sample_enabled:
                        access_model_resource_instance.sample_enabled = resources.sample_enabled
                        access_model_resource_instance.sample_rows = resources.sample_rows
                        if resources.parameters:
                            access_model_resource_instance.parameters = resources.parameters
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
        raise GraphQLError("Policy with given id does not exist.")


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
            dam_obj = DatasetAccessModel.objects.filter(title__exact=access_model_resource_data.title,
                                                        dataset__catalog__organization=dataset_access_model_instance.dataset.catalog.organization)\
                .exclude(id=dataset_access_model_instance.id)
            if len(dam_obj) >= 1:
                raise GraphQLError(
                    "Dataset Access Model with Same name already exists"
                )
            dataset_access_model_instance.title = access_model_resource_data.title
            dataset_access_model_instance.payment_type = access_model_resource_data.payment_type
            dataset_access_model_instance.payment = None
            if access_model_resource_data.payment:
                dataset_access_model_instance.payment = access_model_resource_data.payment
            dataset_access_model_instance.save()

            # Getting id's that were removed.
            get_all_resources = list(DatasetAccessModelResource.objects.filter(
                dataset_access_model_id=access_model_resource_data.id).values_list("resource_id", flat=True))
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
                    if resources.sample_enabled:
                        access_model_resource_instance.sample_enabled = resources.sample_enabled
                        access_model_resource_instance.sample_rows = resources.sample_rows
                        if resources.parameters:
                            access_model_resource_instance.parameters = resources.parameters
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
                id=access_model_resource_data.dam_id
            )
            access_model_resource_instance = DatasetAccessModelResource.objects.filter(
                dataset_access_model=access_model_map_instance
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
