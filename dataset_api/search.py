from django.conf import settings
from elasticsearch import Elasticsearch
from django.http import HttpResponse
import json

# import warnings
# warnings.filterwarnings("ignore")

from .models import Catalog, Organization, Dataset, Resource

es_client = Elasticsearch(settings.ELASTICSEARCH)
# print(es_client.info())


def index_data(data_obj):
    dataset_id = data_obj.dataset_id
    dataset_instance = Dataset.objects.get(id=dataset_id)
    catalog_instance = Catalog.objects.get(id=dataset_instance.catalog_id)
    org_instance = Organization.objects.get(id=catalog_instance.organization_id)

    doc = {
        "resource_title": data_obj.title,
        "resource_description": data_obj.description,
        "format": data_obj.format,
        "resource_status": data_obj.status,
        "dataset_title": dataset_instance.title,
        "dataset_description": dataset_instance.description,
        "license": dataset_instance.License,
        "geography": dataset_instance.geography,
        "dataset_issued": dataset_instance.issued,
        "dataset_modified": dataset_instance.modified,
        "sector": dataset_instance.sector,
        "access_type": dataset_instance.access_type,
        "action": dataset_instance.action,
        "funnel": dataset_instance.funnel,
        "remote_issued": dataset_instance.remote_issued,
        "remote_modified": dataset_instance.remote_modified,
        "status": dataset_instance.status,
        "period_from": dataset_instance.period_from,
        "period_to": dataset_instance.period_to,
        "update_frequency": dataset_instance.update_frequency,
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
        "format": data_obj.format,
        "resource_status": data_obj.status,
    }

    resp = es_client.update(index="dataset", id=data_obj.id, doc=doc)
    print(resp["result"])


def update_dataset(dataset_obj):
    # Find all related resources.
    resource_obj = Resource.objects.filter(dataset_id=dataset_obj.id)
    print(resource_obj)
    for resources in resource_obj:
        doc = {
            "dataset_title": dataset_obj.title,
            "dataset_description": dataset_obj.description,
            "license": dataset_obj.License,
            "geography": dataset_obj.geography,
            "dataset_issued": dataset_obj.issued,
            "dataset_modified": dataset_obj.modified,
            "sector": dataset_obj.sector,
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


def update_catalog(catalog_obj):
    # Find all related resources.
    dataset_obj = Dataset.objects.filter(catalog_id=catalog_obj.id)
    print(dataset_obj)
    for datasets in dataset_obj:
        resource_obj = Resource.objects.filter(dataset_id=datasets.id)
        print(resource_obj)
        for resources in resource_obj:
            doc = {
                "catalog_title": resources.title,
                "catalog_description": resources.description,
                "catalog_issued": resources.issued,
                "catalog_modified": resources.modified,
            }
            resp = es_client.update(index="dataset", id=resources.id, doc=doc)
            print(resp["result"])


def delete_data(id):
    resp = es_client.delete(index="dataset", id=id)
    print(resp["result"])


def facets(request, query_string="None"):
    response = []
    
    agg = {
        "license": {"terms": {"field": "license.keyword"}},
        "geography": {"terms": {"field": "geography.keyword"}},
        "sector": {"terms": {"field": "sector.keyword"}},
        "format": {"terms": {"field": "format.keyword"}},
    }

    query = {
        "match": {
            "dataset_title": query_string
        }
    }
    
    if query_string != "None":
        resp = es_client.search(
            index="dataset",
            aggs=agg,
            query=query,
            
        )
    else:
        resp = es_client.search(
            index="dataset",
            aggs=agg,
            size=0,
            
        )
    
    response.append({"license": resp['aggregations']['license']['buckets']})
    response.append({"geography": resp['aggregations']['geography']['buckets']})
    response.append({"sector": resp['aggregations']['sector']['buckets']})
    response.append({"format": resp['aggregations']['format']['buckets']})

    return HttpResponse(json.dumps(response))
