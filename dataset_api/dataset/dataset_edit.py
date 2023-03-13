import os

import graphene
from django.core.files import File
from graphql import GraphQLError
from graphql_auth.bases import Output

from dataset_api.models import Dataset
from dataset_api.utils import cloner
from .decorators import (
    map_user_dataset,
)
from DatasetServer import settings
import requests


class EditDatasetInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    new_version_name = graphene.String(required=True)


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
                    #get transformers of the dataset
                    url = f"{settings.PIPELINE_URL}pipeline_filter?datasetId=dataset_data.id"
                    headers = {}
                    response = requests.request("GET", url, headers=headers)   
                    response = response.json()
                    trans_list = []
                    for each in response:
                        if each['resultant_res_id']:
                            trans_list.append({'pipeline_id': each['pipeline_id'], 'dataset_id': dataset_data.id, 'resource_id': each['resource_id'], 'resultant_res_id': each['resultant_res_id'] })
                        else:
                            trans_list.append({'pipeline_id': each['pipeline_id'], 'dataset_id': dataset_data.id, 'resource_id': each['resource_id'], 'resultant_res_id': each['resource_id'] })
                        
                        
                    cloned_id = cloner(Dataset, dataset_instance.id, trans_list)
                    cloned_dataset = Dataset.objects.get(pk=cloned_id)
                    cloned_dataset.status = "DRAFT"
                    cloned_dataset.parent = dataset_instance
                    cloned_dataset.accepted_agreement = File(dataset_instance.accepted_agreement, os.path.basename(
                        dataset_instance.accepted_agreement.name), )
                    cloned_dataset.version_name = dataset_data.new_version_name
                    cloned_dataset.save()
                else:
                    return EditDataset(dataset_id=existing_clone[0].id)
            except Dataset.DoesNotExist as e:
                raise GraphQLError("Cloned dataset does not exists.")
            return EditDataset(dataset_id=cloned_id)


class Mutation(graphene.ObjectType):
    edit_dataset = EditDataset.Field()
