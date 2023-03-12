import graphene
from django.db.models import Prefetch
from graphene_django import DjangoObjectType

from dataset_api.decorators import validate_token_or_none
from dataset_api.models import Dataset, Agreement, DatasetAccessModelRequest, DataRequest, DatasetAccessModel


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
            return DatasetAccessModelRequest.objects.filter(
                access_model_id=self.id
            ).values_list('user').distinct().count()
            # dam_requests = self.datasetaccessmodelrequest_set.all()
            # print(
            #     [
            #         x.datarequest_set.filter(status="FETCHED").count()
            #         for x in dam_requests
            #     ]
            # )
            # return sum(
            #     [
            #         x.datarequest_set.filter(status="FETCHED").count()
            #         for x in dam_requests
            #     ]
            # )
        except (DatasetAccessModelRequest.DoesNotExist, DataRequest.DoesNotExist) as e:
            return 0


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
