import graphene
from django.db.models import Prefetch

from dataset_api.dataset_access_model_resource.schema import DatasetAccessModelType
from dataset_api.decorators import validate_token_or_none
from dataset_api.models import Dataset, Agreement, DatasetAccessModelRequest, DataRequest
from dataset_api.models.DatasetAccessModel import DatasetAccessModel


class Query(graphene.ObjectType):
    dataset_access_model = graphene.List(DatasetAccessModelType, dataset_id=graphene.ID(),
                                         anonymous_users=graphene.List(graphene.String))
    dataset_access_model_by_id = graphene.Field(DatasetAccessModelType, dataset_access_model_id=graphene.ID())

    @validate_token_or_none
    def resolve_dataset_access_model(self, info, dataset_id, username, anonymous_users=[], **kwargs):
        dataset = Dataset.objects.get(id=dataset_id)

        print(anonymous_users)
        if username:
            prefetch_data_requests = Prefetch("datarequest_set",
                                              queryset=DataRequest.objects.filter(default=True, user=username))
            prefetch_agreements = Prefetch("agreements", queryset=Agreement.objects.filter(username=username))
            prefetch_dam_requests = Prefetch("datasetaccessmodelrequest_set",
                                             queryset=DatasetAccessModelRequest.objects.filter(
                                                 user=username).order_by("-modified").prefetch_related(
                                                 prefetch_data_requests))
        else:
            prefetch_agreements = Prefetch("agreements",
                                           queryset=Agreement.objects.filter(
                                               dataset_access_model_request__datarequest__id__in=anonymous_users))
            prefetch_data_requests = Prefetch("datarequest_set",
                                              queryset=DataRequest.objects.filter(default=True, id__in=anonymous_users))
            prefetch_dam_requests = Prefetch("datasetaccessmodelrequest_set",
                                             queryset=DatasetAccessModelRequest.objects.filter(
                                                 datarequest__id__in=anonymous_users).order_by(
                                                 "-modified").prefetch_related(
                                                 prefetch_data_requests))

        return DatasetAccessModel.objects.filter(dataset=dataset).order_by("-modified").prefetch_related(
            prefetch_agreements, prefetch_dam_requests)

    def resolve_dataset_access_model_by_id(self, info, dataset_access_model_id):
        return DatasetAccessModel.objects.get(pk=dataset_access_model_id)
