import os
import graphene
from django.core.files import File
from graphene_django import DjangoObjectType
from graphql_auth.bases import Output
from graphql import GraphQLError

from dataset_api.decorators import validate_token, auth_user_by_org
from dataset_api.models import Dataset
from .decorators import (
    auth_user_action_dataset,
    map_user_dataset,
    auth_query_dataset,
    get_user_datasets,
)
from dataset_api.utils import cloner


class EditDatasetInput(graphene.InputObjectType):
    id = graphene.ID(required=True)


class EditDataset(Output, graphene.Mutation):
    class Arguments:
        dataset_data = EditDatasetInput()

    dataset_id = graphene.ID()

    @staticmethod
    # @validate_token
    # @auth_user_action_dataset(action="create_dataset")
    @map_user_dataset
    def mutate(
        root,
        info,
        dataset_data: EditDatasetInput = None,
    ):
        try:
            dataset_instance = Dataset.objects.get(pk=dataset_data.id)
        except Dataset.DoesNotExist as e:
            raise GraphQLError("Dataset does not exists.")

        if dataset_instance.status != "PUBLISHED":
            print("---unpublished---")
            return EditDataset(dataset_id=dataset_data.id)
        else:
            print("----cloned called----")
            
            try:
                existing_clone = Dataset.objects.filter(parent_id=dataset_data.id, status="DRAFT")
                print("exis-clone--", existing_clone)
                if not existing_clone.exists():
                    cloned_id = cloner(Dataset, dataset_instance.id)
                    cloned_resource = Dataset.objects.get(pk=cloned_id)
                    cloned_resource.status = "DRAFT"
                    cloned_resource.parent = dataset_instance
                    cloned_resource.accepted_agreement = File(dataset_instance.accepted_agreement,os.path.basename(dataset_instance.accepted_agreement.path),)
                    cloned_resource.save()
                else:
                    return EditDataset(dataset_id=existing_clone[0].id)
            except Dataset.DoesNotExist as e:
                raise GraphQLError("Cloned dataset does not exists.")
            return EditDataset(dataset_id=cloned_id)


class Mutation(graphene.ObjectType):
    edit_dataset = EditDataset.Field()
