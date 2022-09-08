from django.conf import settings
from elasticsearch import Elasticsearch

# import warnings
# warnings.filterwarnings("ignore")

from .models import Catalog, Organization

es_client = Elasticsearch(settings.ELASTICSEARCH)
#print(es_client.info())

def index_data(data_obj):
    catalog_id = data_obj.catalog_id
    catalog_instance = Catalog.objects.get(id=catalog_id)
    org_instance = Organization.objects.get(id=catalog_instance.organization_id)
    
    doc = {
        "dataset_title": data_obj.title,
        "dataset_description": data_obj.description,
        "license": data_obj.License,
        "geography": data_obj.geography,
        "dataset_issued": data_obj.issued,
        "dataset_modified": data_obj.modified,
        "sector": data_obj.sector,
        "access_type": data_obj.access_type,
        "action": data_obj.action,
        "funnel": data_obj.funnel,
        "remote_issued": data_obj.remote_issued,
        "remote_modified": data_obj.remote_modified,
        "status": data_obj.status,
        "period_from": data_obj.period_from,
        "period_to": data_obj.period_to,
        "update_frequency": data_obj.update_frequency,
        "catalog_title": catalog_instance.title,
        "catalog_description": catalog_instance.description,
        "catalog_issued": catalog_instance.issued,
        "catalog_modified": catalog_instance.modified,
        "org_title": org_instance.title,
        "org_description": org_instance.description,
        "org_issued": org_instance.issued,
        "org_modified": org_instance.modified
    }
    resp = es_client.index(index="dataset", id=data_obj.id, document=doc)
    print(resp['result'])

# def get_doc(doc_id):
#     resp = es_client.get(index="dataset", id=doc_id)
#     #print(resp)
#     print(resp['_source'])

def update_data(data_obj):
    
    doc = {
        "dataset_title": data_obj.title,
        "dataset_description": data_obj.description,
        "license": data_obj.License,
        "geography": data_obj.geography,
        "dataset_issued": data_obj.issued,
        "dataset_modified": data_obj.modified,
        "sector": data_obj.sector,
        "access_type": data_obj.access_type,
        "action": data_obj.action,
        "funnel": data_obj.funnel,
        "remote_issued": data_obj.remote_issued,
        "remote_modified": data_obj.remote_modified,
        "status": data_obj.status,
        "period_from": data_obj.period_from,
        "period_to": data_obj.period_to,
        "update_frequency": data_obj.update_frequency,
    }
    
    resp = es_client.update(index="dataset", id=data_obj.id, doc=doc)
    print(resp['result'])

# def delete_doc(data_obj):
#     doc_id = data_obj.id

#     resp = es_client.delete(index="dataset", id=data_obj.id)
#     print(resp['result'])