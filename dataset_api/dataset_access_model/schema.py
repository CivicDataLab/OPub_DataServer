import graphene
from django.db.models import Prefetch

from dataset_api.dataset_access_model_resource.schema import DatasetAccessModelType
from dataset_api.decorators import validate_token_or_none
from dataset_api.models.DatasetAccessModel import DatasetAccessModel
from dataset_api.models import Dataset, Agreement, DatasetAccessModelRequest


class Query(graphene.ObjectType):
    dataset_access_model = graphene.List(DatasetAccessModelType, dataset_id=graphene.ID())
    dataset_access_model_by_id = graphene.Field(DatasetAccessModelType, dataset_access_model_id=graphene.ID())

    @validate_token_or_none
    def resolve_dataset_access_model(self, info, dataset_id, username, **kwargs):
        try:
            dataset = Dataset.objects.get(id=dataset_id)
        except Dataset.DoesNotExist as e:
            return {"success": False,
                    "errors": {"organization_id": [{"message": "Dataset with id not found", "code": "404"}]}}
        if username:
            prefetch_agreements = Prefetch("agreements", queryset=Agreement.objects.filter(username=username))
            prefetch_dam_requests = Prefetch("datasetaccessmodelrequest_set",
                                             queryset=DatasetAccessModelRequest.objects.filter(user=username))
            return DatasetAccessModel.objects.filter(dataset=dataset).order_by("-modified").prefetch_related(
                prefetch_agreements, prefetch_dam_requests)
        # TODO: don't send requests and agreements when non logged in
        return DatasetAccessModel.objects.filter(dataset=dataset).order_by("-modified")

    def resolve_dataset_access_model_by_id(self, info, dataset_access_model_id):
        return DatasetAccessModel.objects.get(pk=dataset_access_model_id)
