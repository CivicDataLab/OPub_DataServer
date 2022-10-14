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
)

es_client = Elasticsearch(settings.ELASTICSEARCH)
# print(es_client.info())

# TODO: New flow for rating, only update will be there.
def index_data(dataset_obj):
    doc = {
        "dataset_title": dataset_obj.title,
        "dataset_description": dataset_obj.description,
        "dataset_id": dataset_obj.id,
        "action": dataset_obj.action,
        "funnel": dataset_obj.funnel,
        "status": dataset_obj.status,
        "period_from": dataset_obj.period_from,
        "period_to": dataset_obj.period_to,
        "update_frequency": dataset_obj.update_frequency,
        "dataset_type": dataset_obj.dataset_type,
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

    resource_instance = Resource.objects.filter(dataset_id=dataset_obj.id)
    for resources in resource_instance:
        doc["resource_title"] = resources.title
        doc["resource_description"] = resources.description
        doc["resource_status"] = resources.status
        # Checks based on datasets_type.
        if dataset_obj.dataset_type == "API":
            try:
                api_details_obj = APIDetails.objects.get(resource_id=resources.id)
                doc["auth_required"] = api_details_obj.auth_required
                doc["auth_type"] = api_details_obj.api_source.auth_type
            except APIDetails.DoesNotExist as e:
                pass
        else:
            try:
                file_details_obj = FileDetails.objects.get(resource_id=resources.id)
                doc["format"] = file_details_obj.format
            except FileDetails.DoesNotExist as e:
                pass

        # Check if Resource already exists.
        resp = es_client.exists(index="dataset", id=resources.id)
        if resp:
            # Delete the Resource.
            resp = es_client.delete(index="dataset", id=resources.id)
            print(resp["result"])
        # Index the Resource.
        resp = es_client.index(index="dataset", id=resources.id, document=doc)
        print(resp["result"])


# def get_doc(doc_id):
#     resp = es_client.get(index="dataset", id=doc_id)
#     #print(resp)
#     print(resp['_source'])


def delete_data(id):
    resp = es_client.delete(index="dataset", id=id)
    print(resp["result"])


def facets(request):
    filters = []  # List of queries for elasticsearch to filter up on.
    facet = ["license", "geography", "sector", "format", "status", "rating"]
    size = request.GET.get("size", "10")
    paginate_from = request.GET.get("from", "0")
    query_string = request.GET.get("q")
    sort_order = request.GET.get("sort", None)
    org = request.GET.get("organization", None)
    start_date = request.GET.get("start_date", None)
    end_date = request.GET.get("end_date", None)

    if sort_order:
        if sort_order == "last_modified":
            sort_mapping = {"dataset_modified": {"order": "desc"}}
        else:
            sort_mapping = {"resource_title.keyword": {"order": sort_order}}
    else:
        sort_mapping = {}

    # Creating query for faceted search (filters).
    for value in facet:
        if request.GET.get(value):
            filters.append({"match": {f"{value}": request.GET.get(value)}})
    if org:
        filters.append({"match": {"org_title": {"query": org, "operator": "AND"}}})
    if start_date and end_date:
        filters.append(
            {
                "bool": {
                    "must_not": [
                        {"range": {"period_to": {"lte": start_date}}},
                        {"range": {"period_from": {"gte": end_date}}},
                    ]
                }
            }
        )

    # Query for aggregations (facets).
    agg = {
        "license": {"terms": {"field": "license.keyword"}},
        "geography": {"terms": {"field": "geography.keyword"}},
        "sector": {"terms": {"field": "sector.keyword"}},
        "format": {"terms": {"field": "format.keyword"}},
        "status": {"terms": {"field": "status.keyword"}},
        "rating": {"terms": {"field": "rating.keyword"}},
        "organization": {"terms": {"field": "org_title.keyword"}},
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
            return HttpResponse(json.dumps(resp))
        else:
            # For getting facets.
            resp = es_client.search(index="dataset", aggs=agg, size=0)
            return HttpResponse(json.dumps(resp))
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
        return HttpResponse(json.dumps(resp["hits"]))


def search(request):
    query_string = request.GET.get("q", None)
    size = request.GET.get("size", "10")
    paginate_from = request.GET.get("from", "0")
    sort_order = request.GET.get("sort", None)

    if sort_order:
        if sort_order == "last_modified":
            sort_mapping = {"dataset_modified": {"order": "desc"}}
        else:
            sort_mapping = {"resource_title.keyword": {"order": sort_order}}
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
    resource_obj = Resource.objects.all()
    doc = {}
    for resources in resource_obj:
        if resources.dataset.status == "PUBLISHED":
            doc["dataset_title"] = resources.dataset.title
            doc["dataset_description"] = resources.dataset.description
            doc["dataset_id"] = resources.dataset.id
            doc["action"] = resources.dataset.action
            doc["funnel"] = resources.dataset.funnel
            doc["status"] = resources.dataset.status
            doc["period_from"] = resources.dataset.period_from
            doc["period_to"] = resources.dataset.period_to
            doc["update_frequency"] = resources.dataset.update_frequency
            doc["dataset_type"] = resources.dataset.dataset_type
            doc["resource_title"] = resources.title
            doc["resource_description"] = resources.description
            doc["resource_status"] = resources.status

            geography = resources.dataset.geography.all()
            sector = resources.dataset.sector.all()
            dataset_geography = []
            dataset_sector = []
            for geo in geography:
                dataset_geography.append(geo.name)
            for sec in sector:
                dataset_sector.append(sec.name)
            doc["geography"] = dataset_geography
            doc["sector"] = dataset_sector

            catalog_instance = Catalog.objects.get(id=resources.dataset.catalog_id)
            doc["catalog_title"] = catalog_instance.title
            doc["catalog_description"] = catalog_instance.description

            org_instance = Organization.objects.get(id=catalog_instance.organization_id)
            doc["org_title"] = org_instance.title
            doc["org_description"] = org_instance.description
            doc["org_id"] = catalog_instance.organization_id

            # Checks based on datasets_type.
            if resources.dataset.dataset_type == "API":
                try:
                    api_details_obj = APIDetails.objects.get(resource_id=resources.id)
                    doc["auth_required"] = api_details_obj.auth_required
                    doc["auth_type"] = api_details_obj.api_source.auth_type
                except APIDetails.DoesNotExist as e:
                    pass
            else:
                try:
                    file_details_obj = FileDetails.objects.get(resource_id=resources.id)
                    doc["format"] = file_details_obj.format
                except FileDetails.DoesNotExist as e:
                    pass

            print("Resource_id --", resources.id)
            # if es_client.exists(index="dataset", id=resources.id):
            #     pass
            # else:
            resp = es_client.index(index="dataset", id=resources.id, document=doc)
            print("Index --", resp["result"])
