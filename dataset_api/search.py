from django.conf import settings
from elasticsearch import Elasticsearch
from django.http import HttpResponse
import json

# from django.utils.datastructures import MultiValueDictKeyError

# import warnings
# warnings.filterwarnings("ignore")

from .models import (
    Catalog,
    Organization,
    Resource,
    FileDetails,
    APIDetails,
    Dataset,
    DatasetAccessModel,
)
from .utils import dataset_slug

es_client = Elasticsearch(settings.ELASTICSEARCH)


# print(es_client.info())

# TODO: New flow for rating, only update will be there.
def index_data(dataset_obj):
    doc = {
        "dataset_title": dataset_obj.title,
        "dataset_description": dataset_obj.description,
        "action": dataset_obj.action,
        "funnel": dataset_obj.funnel,
        "period_from": dataset_obj.period_from,
        "period_to": dataset_obj.period_to,
        "update_frequency": dataset_obj.update_frequency,
        "dataset_type": dataset_obj.dataset_type,
        "remote_issued": dataset_obj.remote_issued,
        "remote_modified": dataset_obj.remote_modified,
        "slug": dataset_slug(dataset_obj.id),
    }

    geography = dataset_obj.geography.all()
    sector = dataset_obj.sector.all()
    dataset_geography = []
    dataset_sector = []
    for geo in geography:
        dataset_geography.append(geo.name)
    for sec in sector:
        dataset_sector.append(sec.name)
    doc["geography"] = dataset_geography
    doc["sector"] = dataset_sector

    catalog_instance = Catalog.objects.get(id=dataset_obj.catalog_id)
    doc["catalog_title"] = catalog_instance.title
    doc["catalog_description"] = catalog_instance.description

    org_instance = Organization.objects.get(id=catalog_instance.organization_id)
    doc["org_title"] = org_instance.title
    doc["org_description"] = org_instance.description
    doc["org_id"] = catalog_instance.organization_id
    doc["org_logo"] = str(org_instance.logo) if org_instance.logo else ""

    resource_instance = Resource.objects.filter(dataset_id=dataset_obj.id)
    resource_title = []
    resource_description = []
    auth_required = []
    auth_type = []
    format = []
    for resources in resource_instance:
        resource_title.append(resources.title)
        resource_description.append(resources.description)
        # Checks based on datasets_type.
        if dataset_obj.dataset_type == "API":
            try:
                api_details_obj = APIDetails.objects.get(resource_id=resources.id)
                auth_required.append(api_details_obj.auth_required)
                auth_type.append(api_details_obj.api_source.auth_type)
            except APIDetails.DoesNotExist as e:
                pass
        else:
            try:
                file_details_obj = FileDetails.objects.get(resource_id=resources.id)
                format.append(file_details_obj.format)
            except FileDetails.DoesNotExist as e:
                pass
    # Index all resources of a dataset.
    doc["resource_title"] = resource_title
    doc["resource_description"] = resource_description
    if auth_required:
        doc["auth_required"] = auth_required
    if auth_type:
        doc["auth_type"] = auth_type
    if format:
        doc["format"] = format

    # Index Data Access Model.
    dam_instance = DatasetAccessModel.objects.filter(dataset_id=dataset_obj.id)
    data_access_model_id = []
    data_access_model_title = []
    data_access_model_type = []
    for dam in dam_instance:
        data_access_model_id.append(dam.data_access_model.id)
        data_access_model_title.append(dam.data_access_model.title)
        data_access_model_type.append(dam.data_access_model.type)

    if data_access_model_id:
        doc["data_access_model_id"] = data_access_model_id
    if data_access_model_title:
        doc["data_access_model_title"] = data_access_model_title
    if data_access_model_type:
        doc["data_access_model_type"] = data_access_model_type

    # Check if Dataset already exists.
    resp = es_client.exists(index="dataset", id=dataset_obj.id)
    if resp:
        # Delete the Dataset.
        resp = es_client.delete(index="dataset", id=dataset_obj.id)
        # print(resp["result"])
    # Index the Dataset.
    resp = es_client.index(index="dataset", id=dataset_obj.id, document=doc)
    # print(resp["result"])
    return resp["result"]


# def get_doc(doc_id):
#     resp = es_client.get(index="dataset", id=doc_id)
#     #print(resp)
#     print(resp['_source'])


def delete_data(id):
    resp = es_client.delete(index="dataset", id=id)
    print(resp["result"])


def facets(request):
    filters = []  # List of queries for elasticsearch to filter up on.
    selected_facets = []  # List of facets that are selected.
    facet = ["license", "geography", "format", "status", "rating", "sector"]
    size = request.GET.get("size", "5")
    paginate_from = request.GET.get("from", "0")
    query_string = request.GET.get("q")
    sort_order = request.GET.get("sort", None)
    org = request.GET.get("organization", None)
    start_duration = request.GET.get("start_duration", None)
    end_duration = request.GET.get("end_duration", None)

    if sort_order:
        if sort_order == "last_modified":
            sort_mapping = {"remote_modified": {"order": "desc"}}
        else:
            sort_mapping = {"dataset_title.keyword": {"order": sort_order}}
    else:
        sort_mapping = {}

    # Creating query for faceted search (filters).
    for value in facet:
        if request.GET.get(value):
            filters.append({"match": {f"{value}": request.GET.get(value).replace("||", " ")}})
            selected_facets.append({f"{value}": request.GET.get(value).split("||")})
    if org:
        filters.append({"match": {"org_title": {"query": org, "operator": "AND"}}})
        selected_facets.append({"organization": org.split('||')})

    if start_duration and end_duration:
        filters.append(
            {
                "bool": {
                    "must_not": [
                        {"range": {"period_to": {"lte": start_duration}}},
                        {"range": {"period_from": {"gte": end_duration}}},
                    ]
                }
            }
        )
        selected_facets.append({"start_duration": start_duration})
        selected_facets.append({"end_duration": end_duration})

    # Query for aggregations (facets).
    agg = {
        "license": {"terms": {"field": "license.keyword"}},
        "geography": {"terms": {"field": "geography.keyword"}},
        "sector": {"terms": {"field": "sector.keyword"}},
        "format": {"terms": {"field": "format.keyword"}},
        "status": {"terms": {"field": "status.keyword"}},
        "rating": {"terms": {"field": "rating.keyword"}},
        "organization": {"global": {}, "aggs": {"all": {"terms": {"field": "org_title.keyword"}}}},
        "duration": {"global": {}, "aggs": {"min": {"min": {"field": "period_from", "format": "yyyy-MM-dd"}},
                                            "max": {"max": {"field": "period_to", "format": "yyyy-MM-dd"}}}},
    }
    if not query_string:
        # For filter search
        if len(request.GET.keys()) >= 1:
            query = {"bool": {"must": filters}}
            resp = es_client.search(
                index="dataset",
                aggs=agg,
                query=query,
                size=size,
                from_=paginate_from,
                sort=sort_mapping,
            )
        else:
            # For getting facets.
            resp = es_client.search(index="dataset", aggs=agg, size=0)
    else:
        # For faceted search with query string.
        filters.append(
            {"match": {"dataset_title": {"query": query_string, "operator": "AND"}}}
        )
        query = {"bool": {"must": filters}}
        resp = es_client.search(
            index="dataset",
            aggs=agg,
            query=query,
            size=size,
            from_=paginate_from,
            sort=sort_mapping,
        )
    resp["selected_facets"] = selected_facets
    return HttpResponse(json.dumps(resp))


def search(request):
    query_string = request.GET.get("q", None)
    size = request.GET.get("size", "5")
    paginate_from = request.GET.get("from", "0")
    sort_order: str = request.GET.get("sort", None)

    if sort_order:
        if sort_order == "last_modified":
            sort_mapping = {"remote_modified": {"order": "desc"}}
        else:
            sort_mapping = {"dataset_title.keyword": {"order": sort_order}}
    else:
        sort_mapping = {}

    if query_string:
        query = {"match": {"dataset_title": {"query": query_string, "operator": "AND"}}}
    else:
        query = {"match_all": {}}

    resp = es_client.search(
        index="dataset", query=query, size=size, from_=paginate_from, sort=sort_mapping
    )
    return HttpResponse(json.dumps(resp["hits"]))


def more_like_this(request):
    id = request.GET.get("q", None)
    if id:
        query = {
            "more_like_this": {
                "like": [{"_index": "dataset", "_id": id}],
                "min_term_freq": 1,
                "max_query_terms": 10,
            }
        }
        resp = es_client.search(index="dataset", query=query)
        return HttpResponse(json.dumps(resp["hits"]))


def reindex_data():
    dataset_obj = Dataset.objects.all()
    for datasets in dataset_obj:
        if datasets.status == "PUBLISHED":
            resp = index_data(datasets)
            if resp == "created":
                print("Dataset_id --", datasets.id)
            else:
                print("Re-indexing failed!")
