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
    Dataset,
    Resource,
    DatasetRatings,
    APISource,
    APIResource,
)

es_client = Elasticsearch(settings.ELASTICSEARCH)
# print(es_client.info())


def index_data(data_obj):
    dataset_id = data_obj.dataset_id

    dataset_instance = Dataset.objects.get(id=dataset_id)
    geography = dataset_instance.geography.all()
    sector = dataset_instance.sector.all()
    dataset_geography = []
    dataset_sector = []
    for geo in geography:
        dataset_geography.append(geo.name)
    for sec in sector:
        dataset_sector.append(sec.name)
    dataset_rating = DatasetRatings.objects.filter(dataset_id=dataset_id)
    if dataset_rating.exists():
        rating = dataset_rating[0].data_quality
    else:
        rating = ""
    catalog_instance = Catalog.objects.get(id=dataset_instance.catalog_id)
    org_instance = Organization.objects.get(id=catalog_instance.organization_id)

    doc = {
        "resource_title": data_obj.title,
        "resource_description": data_obj.description,
        "format": data_obj.filedetails.format,
        "resource_status": data_obj.status,
        "dataset_title": dataset_instance.title,
        "dataset_description": dataset_instance.description,
        "dataset_id": dataset_id,
        "license": dataset_instance.License,
        "geography": dataset_geography,
        "dataset_issued": dataset_instance.issued,
        "dataset_modified": dataset_instance.modified,
        "sector": dataset_sector,
        "access_type": dataset_instance.access_type,
        "action": dataset_instance.action,
        "funnel": dataset_instance.funnel,
        "remote_issued": dataset_instance.remote_issued,
        "remote_modified": dataset_instance.remote_modified,
        "status": dataset_instance.status,
        "period_from": dataset_instance.period_from,
        "period_to": dataset_instance.period_to,
        "update_frequency": dataset_instance.update_frequency,
        "rating": rating,
        "catalog_title": catalog_instance.title,
        "catalog_description": catalog_instance.description,
        "catalog_issued": catalog_instance.issued,
        "catalog_modified": catalog_instance.modified,
        "org_title": org_instance.title,
        "org_description": org_instance.description,
        "org_issued": org_instance.issued,
        "org_modified": org_instance.modified,
    }
    resp = es_client.index(index="dataset", id=data_obj.id, document=doc)
    print(resp["result"])


# def get_doc(doc_id):
#     resp = es_client.get(index="dataset", id=doc_id)
#     #print(resp)
#     print(resp['_source'])


def update_data(data_obj):

    doc = {
        "resource_title": data_obj.title,
        "resource_description": data_obj.description,
        "format": data_obj.filedetails.format,
        "resource_status": data_obj.status,
    }

    resp = es_client.update(index="dataset", id=data_obj.id, doc=doc)
    print(resp["result"])


def update_dataset(dataset_obj):
    # Find all related resources.
    resource_obj = Resource.objects.filter(dataset_id=dataset_obj.id)
    for resources in resource_obj:
        geography = dataset_obj.geography.all()
        sector = dataset_obj.sector.all()
        dataset_geography = []
        dataset_sector = []
        for geo in geography:
            dataset_geography.append(geo.name)
        for sec in sector:
            dataset_sector.append(sec.name)
        doc = {
            "dataset_title": dataset_obj.title,
            "dataset_description": dataset_obj.description,
            "license": dataset_obj.License,
            "geography": dataset_geography,
            "dataset_issued": dataset_obj.issued,
            "dataset_modified": dataset_obj.modified,
            "sector": dataset_sector,
            "access_type": dataset_obj.access_type,
            "action": dataset_obj.action,
            "funnel": dataset_obj.funnel,
            "remote_issued": dataset_obj.remote_issued,
            "remote_modified": dataset_obj.remote_modified,
            "status": dataset_obj.status,
            "period_from": dataset_obj.period_from,
            "period_to": dataset_obj.period_to,
            "update_frequency": dataset_obj.update_frequency,
        }
        resp = es_client.update(index="dataset", id=resources.id, doc=doc)
        print(resp["result"])


def update_rating(rating_obj):
    # Find all related resources.
    dataset_obj = Dataset.objects.get(id=rating_obj.dataset_id)
    resource_obj = Resource.objects.filter(dataset_id=dataset_obj.id)
    for resources in resource_obj:
        print(resources)
        doc = {
            "rating": rating_obj.data_quality,
        }
        resp = es_client.update(index="dataset", id=resources.id, doc=doc)
        print(resp["result"])


def index_api_resource(api_resource_obj):
    dataset_obj = Dataset.objects.get(id=api_resource_obj.dataset_id)
    api_source_obj = APISource.objects.get(id=api_resource_obj.api_source_id)
    resource_obj = Resource.objects.filter(dataset_id=dataset_obj.id)
    for resources in resource_obj:
        doc = {
            "api_resource_title": api_resource_obj.title,
            "api_resource_description": api_resource_obj.description,
            "api_resource_status": api_resource_obj.status,
            "api_resource_urlpath": api_resource_obj.url_path,
            "api_resource_auth_req": api_resource_obj.auth_required,
            "api_resource_response_type": api_resource_obj.response_type,
            "api_source_title": api_source_obj.title,
            "api_source_description": api_source_obj.description,
            "api_source_baseurl": api_source_obj.base_url,
            "api_source_version": api_source_obj.api_version,
            "api_source_auth_loc": api_source_obj.auth_loc,
            "api_source_auth_type": api_source_obj.auth_type,
        }
        resp = es_client.update(index="dataset", id=resources.id, doc=doc)
        print(resp["result"])


def update_api_resource(api_resource_obj):
    dataset_obj = Dataset.objects.get(id=api_resource_obj.dataset_id)
    resource_obj = Resource.objects.filter(dataset_id=dataset_obj.id)
    for resources in resource_obj:
        doc = {
            "api_resource_title": api_resource_obj.title,
            "api_resource_description": api_resource_obj.description,
            "api_resource_status": api_resource_obj.status,
            "api_resource_urlpath": api_resource_obj.url_path,
            "api_resource_auth_req": api_resource_obj.auth_required,
            "api_resource_response_type": api_resource_obj.response_type,
        }
        resp = es_client.update(index="dataset", id=resources.id, doc=doc)
        print(resp["result"])


def delete_api_resource(api_resource_obj):
    dataset_obj = Dataset.objects.get(id=api_resource_obj.dataset_id)
    resource_obj = Resource.objects.filter(dataset_id=dataset_obj.id)
    for resources in resource_obj:
        doc = {
            "api_resource_title": "",
            "api_resource_description": "",
            "api_resource_status": "",
            "api_resource_urlpath": "",
            "api_resource_auth_req": "",
            "api_resource_response_type": "",
        }
        resp = es_client.update(index="dataset", id=resources.id, doc=doc)
        print(resp["result"])


# def update_catalog(catalog_obj):
#     # Find all related resources.
#     dataset_obj = Dataset.objects.filter(catalog_id=catalog_obj.id)
#     print(dataset_obj)
#     for datasets in dataset_obj:
#         resource_obj = Resource.objects.filter(dataset_id=datasets.id)
#         print(resource_obj)
#         for resources in resource_obj:
#             doc = {
#                 "catalog_title": resources.title,
#                 "catalog_description": resources.description,
#                 "catalog_issued": resources.issued,
#                 "catalog_modified": resources.modified,
#             }
#             resp = es_client.update(index="dataset", id=resources.id, doc=doc)
#             print(resp["result"])


def delete_data(id):
    resp = es_client.delete(index="dataset", id=id)
    print(resp["result"])


def facets(request):
    filters = []  # List of queries for elasticsearch to filter up on.
    facet = [
        "license",
        "geography",
        "sector",
        "format",
        "status",
        "rating",
        "query_string",
    ]
    size = request.GET.get("size", "10")
    paginate_from = request.GET.get("from", "0")
    query_string = request.GET.get("q")

    for value in facet:
        if request.GET.get(value):
            filters.append({"match": {f"{value}": request.GET.get(value)}})

    agg = {
        "license": {"terms": {"field": "license.keyword"}},
        "geography": {"terms": {"field": "geography.keyword"}},
        "sector": {"terms": {"field": "sector.keyword"}},
        "format": {"terms": {"field": "format.keyword"}},
        "status": {"terms": {"field": "status.keyword"}},
        "rating": {"terms": {"field": "rating.keyword"}},
    }

    if not query_string:
        # For filter search
        if len(request.GET.keys()) >= 1:
            query = {"bool": {"must": filters}}
            resp = es_client.search(
                index="dataset", aggs=agg, query=query, size=size, from_=paginate_from
            )
            return HttpResponse(json.dumps(resp))
        else:
            # For getting facets.
            resp = es_client.search(index="dataset", aggs=agg, size=0)
            return HttpResponse(json.dumps(resp))
    else:
        # For faceted search with query string.
        query = {"bool": {"must": filters}}
        resp = es_client.search(
            index="dataset", aggs=agg, query=query, size=size, from_=paginate_from
        )
        return HttpResponse(json.dumps(resp))


def search(request):
    query_string = request.GET.get("q", "")
    size = request.GET.get("size", "10")
    paginate_from = request.GET.get("from", "0")

    if query_string != "":
        query = {"match": {"dataset_title": {"query": query_string, "operator": "AND"}}}
    else:
        query = {"match_all": {}}

    resp = es_client.search(
        index="dataset", query=query, size=size, from_=paginate_from
    )
    return HttpResponse(json.dumps(resp["hits"]))


def reindex_data():
    resource_obj = Resource.objects.all()
    # print(resource_obj)
    for resources in resource_obj:
        print("Dataset_id --", resources.dataset_id)
        dataset_instance = Dataset.objects.get(id=resources.dataset_id)
        geography = dataset_instance.geography.all()
        # print(geography)
        sector = dataset_instance.sector.all()
        # print(sector)
        dataset_geography = []
        dataset_sector = []
        if geography.exists():
            for geo in geography:
                dataset_geography.append(geo.name)
        if sector.exists():
            for sec in sector:
                dataset_sector.append(sec.name)
        dataset_rating = DatasetRatings.objects.filter(dataset_id=resources.dataset_id)
        # print(dataset_rating)
        if dataset_rating.exists():
            rating = dataset_rating[0].data_quality
        else:
            rating = ""
        # print(resources.dataset_id)
        try:
            api_resource_obj = APIResource.objects.filter(
                dataset_id=resources.dataset_id
            )
            api_resource_title = []
            api_resource_description = []
            api_resource_status = []
            api_resource_urlpath = []
            api_resource_auth_req = []
            api_resource_response_type = []
            api_source_title = []
            api_source_description = []
            api_source_baseurl = []
            api_source_version = []
            api_source_auth_loc = []
            api_source_auth_type = []

            for api_resources in api_resource_obj:
                api_source_obj = APISource.objects.get(id=api_resources.api_source_id)
                api_resource_title.append(api_resources.title)
                api_resource_description.append(api_resources.description)
                api_resource_status.append(api_resources.status)
                api_resource_urlpath.append(api_resources.url_path)
                api_resource_auth_req.append(api_resources.auth_required)
                api_resource_response_type.append(api_resources.response_type)
                api_source_title.append(api_source_obj.title)
                api_source_description.append(api_source_obj.description)
                api_source_baseurl.append(api_source_obj.base_url)
                api_source_version.append(api_source_obj.api_version)
                api_source_auth_loc.append(api_source_obj.auth_loc)
                api_source_auth_type.append(api_source_obj.auth_type)
        except (APIResource.DoesNotExist, IndexError) as e:
            print(e)
        catalog_instance = Catalog.objects.get(id=dataset_instance.catalog_id)
        org_instance = Organization.objects.get(id=catalog_instance.organization_id)

        doc = {
            "resource_title": resources.title,
            "resource_description": resources.description,
            "format": resources.format,
            "resource_status": resources.status,
            "dataset_title": dataset_instance.title,
            "dataset_description": dataset_instance.description,
            "dataset_id": resources.dataset_id,
            "license": dataset_instance.License,
            "geography": dataset_geography,
            "dataset_issued": dataset_instance.issued,
            "dataset_modified": dataset_instance.modified,
            "sector": dataset_sector,
            "access_type": dataset_instance.access_type,
            "action": dataset_instance.action,
            "funnel": dataset_instance.funnel,
            "remote_issued": dataset_instance.remote_issued,
            "remote_modified": dataset_instance.remote_modified,
            "status": dataset_instance.status,
            "period_from": dataset_instance.period_from,
            "period_to": dataset_instance.period_to,
            "update_frequency": dataset_instance.update_frequency,
            "rating": rating,
            "catalog_title": catalog_instance.title,
            "catalog_description": catalog_instance.description,
            "catalog_issued": catalog_instance.issued,
            "catalog_modified": catalog_instance.modified,
            "org_title": org_instance.title,
            "org_description": org_instance.description,
            "org_issued": org_instance.issued,
            "org_modified": org_instance.modified,
            "api_resource_title": api_resource_title,
            "api_resource_description": api_resource_description,
            "api_resource_status": api_resource_status,
            "api_resource_urlpath": api_resource_urlpath,
            "api_resource_auth_req": api_resource_auth_req,
            "api_resource_response_type": api_resource_response_type,
            "api_source_title": api_source_title,
            "api_source_description": api_source_description,
            "api_source_baseurl": api_source_baseurl,
            "api_source_version": api_source_version,
            "api_source_auth_loc": api_source_auth_loc,
            "api_source_auth_type": api_source_auth_type,
        }
        print("Resource_id --", resources.id)
        # if es_client.exists(index="dataset", id=resources.id):
        #     pass
        # else:
        resp = es_client.index(index="dataset", id=resources.id, document=doc)
        print("Index --", resp["result"])
