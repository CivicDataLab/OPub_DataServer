import json

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from elasticsearch import Elasticsearch

from .models import (
    Catalog,
    Organization,
    OrganizationCreateRequest,
    Resource,
    FileDetails,
    APIDetails,
    Dataset,
    DatasetAccessModel,
    DatasetAccessModelRequest,
)
from .utils import dataset_slug, get_average_rating
from .enums import DataType

# from django.utils.datastructures import MultiValueDictKeyError

es_client = Elasticsearch(settings.ELASTICSEARCH)


# TODO: New flow for rating, only update will be there.
def index_data(dataset_obj):
    if not dataset_obj.status == "PUBLISHED":
        return
    doc = {
        "dataset_title": dataset_obj.title,
        "dataset_description": dataset_obj.description,
        "action": dataset_obj.action,
        "funnel": dataset_obj.funnel,
        "issued": dataset_obj.issued,
        "period_from": dataset_obj.period_from,
        "period_to": dataset_obj.period_to,
        "update_frequency": dataset_obj.update_frequency,
        "dataset_type": dataset_obj.dataset_type,
        "remote_issued": dataset_obj.remote_issued,
        "remote_modified": dataset_obj.remote_modified,
        "published_date": dataset_obj.published_date,
        "last_updated": dataset_obj.last_updated,
        "modified": dataset_obj.modified,
        "slug": dataset_slug(dataset_obj.id),
        "highlights": dataset_obj.highlights or [],
        "download_count": dataset_obj.download_count,
        "average_rating": get_average_rating(dataset_obj),
        "hvd_rating": dataset_obj.hvd_rating,
        "resource_count": Resource.objects.filter(dataset=dataset_obj).count(),
        "dynamic_date": dataset_obj.is_datedynamic
    }

    geography = dataset_obj.geography.all()
    sector = dataset_obj.sector.all()
    tags = dataset_obj.tags.all()
    dataset_geography = []
    dataset_sector = []
    dataset_tag = []
    for geo in geography:
        dataset_geography.append(geo.name)
    for sec in sector:
        dataset_sector.append(sec.name)
    for tag in tags:
        dataset_tag.append(tag.name)
    doc["geography"] = dataset_geography
    doc["sector"] = dataset_sector
    doc["tags"] = dataset_tag

    catalog_instance = Catalog.objects.get(id=dataset_obj.catalog_id)
    doc["catalog_title"] = catalog_instance.title
    doc["catalog_description"] = catalog_instance.description

    org_instance = Organization.objects.get(id=catalog_instance.organization_id)
    doc["org_title"] = org_instance.title
    doc["org_description"] = org_instance.description
    doc["org_types"] = org_instance.organization_types
    doc["org_id"] = catalog_instance.organization_id
    doc["org_logo"] = str(org_instance.logo) if org_instance.logo else ""
    update_organization_index(
        OrganizationCreateRequest.objects.get(organization_ptr_id=org_instance.id)
    )
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
        if dataset_obj.dataset_type == DataType.API.value:
            try:
                api_details_obj = APIDetails.objects.get(resource_id=resources.id)
                auth_required.append(api_details_obj.auth_required)
                auth_type.append(api_details_obj.api_source.auth_type)
                format.append(api_details_obj.response_type)
            except APIDetails.DoesNotExist as e:
                pass
        elif dataset_obj.dataset_type == DataType.FILE.value:
            try:
                file_details_obj = FileDetails.objects.get(resource_id=resources.id)
                format.append(file_details_obj.format)
            except FileDetails.DoesNotExist as e:
                pass
        else:
            format.append("EXTERNAL LINK")
    # Index all resources of a dataset.
    doc["resource_title"] = resource_title
    doc["resource_description"] = resource_description
    # if auth_required:
    #     doc["auth_required"] = auth_required
    # if auth_type:
    #     doc["auth_type"] = auth_type
    # if format:
    #     doc["format"] = format

    # Index Data Access Model.
    # dam_instances = DatasetAccessModel.objects.filter(dataset=dataset_obj)
    # data_access_model_ids = []
    # data_access_model_titles = []
    # data_access_model_types = []
    # dataset_access_models = []
    # license = []
    # for dam in dam_instances:
    #     data_access_model_ids.append(dam.data_access_model.id)
    #     data_access_model_titles.append(dam.data_access_model.title)
    #     data_access_model_types.append(dam.data_access_model.type)
    #     license.append(dam.data_access_model.license.title)
    #     dataset_access_models.append(
    #         {
    #             "id": dam.id,
    #             "type": dam.data_access_model.type,
    #             "payment_type": dam.payment_type,
    #             "payment": dam.payment,
    #         }
    #     )
    # doc["dataset_access_models"] = dataset_access_models
    # doc["data_access_model_id"] = data_access_model_ids
    # doc["data_access_model_title"] = data_access_model_titles
    # doc["data_access_model_type"] = data_access_model_types
    # doc["license"] = license

    # Check if Dataset already exists.
    resp = es_client.exists(index="dataset", id=dataset_obj.id)
    if resp:
        # Delete the Dataset.
        resp = es_client.delete(index="dataset", id=dataset_obj.id)
        # print(resp["result"])
    # Index the Dataset.
    resp = es_client.index(index="dataset", id=dataset_obj.id, document=doc)
    update_organization_index(
        OrganizationCreateRequest.objects.get(organization_ptr_id=org_instance.id)
    )
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
    facet = [
        "license",
        "geography",
        "format",
        "status",
        "rating",
        "sector",
        # "org_types",
    ]
    # dam_type = request.GET.get("type")
    # payment_type = request.GET.get("payment_type")
    size = request.GET.get("size")
    if not size:
        size = 5
    paginate_from = request.GET.get("from", 0)
    query_string = request.GET.get("q")
    sort_by = request.GET.get("sort_by", None)
    sort_order = request.GET.get("sort", "")
    if sort_order == "":
        sort_order = "desc"
    org = request.GET.get("organization", None)
    start_duration = request.GET.get("start_duration", None)
    end_duration = request.GET.get("end_duration", None)
    # print(sort_by, sort_order)
    if sort_by and sort_order:
        if sort_by == "modified":
            sort_mapping = {"modified": {"order": sort_order}}
        elif sort_by == "rating":
            sort_mapping = {"average_rating": {"order": sort_order}}
        elif sort_by == "provider":
            sort_mapping = {"org_title.keyword": {"order": sort_order}}
        elif sort_by == "recent":
            sort_mapping = {"last_updated": {"order": "desc"}}
        elif sort_by == "relevance":
            sort_mapping = {}
        elif sort_by == "downloads":
            sort_mapping = {"download_count": {"order": "desc"}}
        else:
            sort_mapping = {"dataset_title.keyword": {"order": sort_order}}
    else:
        sort_mapping = {}

    # Creating query for faceted search (filters).
    for value in facet:
        if value == "sector" and request.GET.get(value):
            filters.append(
                {
                    "match": {
                        f"{value}": {
                            "query": request.GET.get(value).replace("||", " "),
                            "operator": "AND",
                        }
                    }
                }
            )
            selected_facets.append({f"{value}": request.GET.get(value).split("||")})
        else:
            if request.GET.get(value):
                filters.append(
                    {"match": {f"{value}": request.GET.get(value).replace("||", " ")}}
                )
                selected_facets.append({f"{value}": request.GET.get(value).split("||")})

    # if dam_type:
    #     filters.append(
    #         {"match": {"dataset_access_models.type": dam_type.replace("||", " ")}}
    #     )
    #     selected_facets.append({"type": dam_type.split("||")})
    # if payment_type:
    #     filters.append(
    #         {
    #             "match": {
    #                 "dataset_access_models.payment_type": payment_type.replace(
    #                     "||", " "
    #                 )
    #             }
    #         }
    #     )
    #     selected_facets.append({"payment_type": payment_type.split("||")})

    if org:
        filters.append({"terms": {"org_title.keyword": org.split("||")}})
        selected_facets.append({"organization": org.split("||")})

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
        # "license": {
        #     "global": {},
        #     "aggs": {"all": {"terms": {"field": "license.keyword", "size": 10000, "order": {"_key" : "asc"}}}},
        # },
        # "license": {"terms": {"field": "license.keyword", "size": 10000}},
        "geography": {
            "global": {},
            "aggs": {"all": {"terms": {"field": "geography.keyword", "size": 10000, "order": {"_key" : "asc"}}}},
        },
        # "geography": {"terms": {"field": "geography.keyword", "size": 10000}},
        "sector": {
            "global": {},
            "aggs": {"all": {"terms": {"field": "sector.keyword", "size": 10000, "order": {"_key" : "asc"}}}},
        },
        # "sector": {"terms": {"field": "sector.keyword", "size": 10000}},
        "format": {
            "global": {},
            "aggs": {"all": {"terms": {"field": "format.keyword", "size": 10000, "order": {"_key" : "asc"}}}},
        },
        # "format": {"terms": {"field": "format.keyword", "size": 10000}},
        "status": {
            "global": {},
            "aggs": {"all": {"terms": {"field": "status.keyword", "size": 10000, "order": {"_key" : "asc"}}}},
        },
        # "status": {"terms": {"field": "status.keyword", "size": 10000}},
        "rating": {
            "global": {},
            "aggs": {"all": {"terms": {"field": "rating.keyword", "size": 10000, "order": {"_key" : "asc"}}}},
        },
        # "rating": {"terms": {"field": "rating.keyword", "size": 10000}},
        # "org_types": {
        #     "global": {},
        #     "aggs": {"all": {"terms": {"field": "org_types.keyword", "size": 10000, "order": {"_key" : "asc"}}}},
        # },
        # "org_types": {"terms": {"field": "org_types.keyword", "size": 10000}},
        "organization": {
            "global": {},
            "aggs": {"all": {"terms": {"field": "org_title.keyword", "size": 10000, "order": {"_key" : "asc"}}}},
        },
        "duration": {
            "global": {},
            "aggs": {
                "min": {"min": {"field": "period_from", "format": "yyyy-MM-dd"}},
                "max": {"max": {"field": "period_to", "format": "yyyy-MM-dd"}},
            },
        },
        # "type": {
        #     "global": {},
        #     "aggs": {"all": {"terms": {"field": "dataset_access_models.type.keyword", "size": 10000, "order": {"_key" : "asc"}}}},
        # },
        # "type": {
        #     "terms": {"field": "dataset_access_models.type.keyword", "size": 10000}
        # },
        # "payment_type": {
        #     "global": {},
        #     "aggs": {"all": {"terms": {"field": "dataset_access_models.payment_type.keyword", "size": 10000, "order": {"_key" : "asc"}}}},
        # },
        # "payment_type": {
        #     "terms": {
        #         "field": "dataset_access_models.payment_type.keyword",
        #         "size": 10000,
        #     }
        # },
    }
    if not query_string:
        # For filter search
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
        # For faceted search with query string.
        filters.append(
            {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "dataset_title": {
                                    "query": query_string,
                                    "operator": "OR",
                                    "fuzziness": "AUTO",
                                    "boost": "2",
                                }
                            }
                        },
                        {"match": {"tags": {"query": query_string, "boost": "1"}}},
                        {"match": {"geography": {"query": query_string, "boost": "1"}}},
                        {
                            "match": {
                                "dataset_description": {
                                    "query": query_string,
                                    "boost": "0.5",
                                }
                            }
                        },
                    ]
                }
            }
        )
        # filters.append({"match_phrase_prefix":{"dataset_title":{"query": query_string}}})
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
    return JsonResponse(resp)  # HttpResponse(json.dumps(resp))


def organization_search(request):
    query_string = request.GET.get("q", None)
    size = request.GET.get("size", 5)
    paginate_from = request.GET.get("from", 0)
    sort_order: str = request.GET.get("sort", None)

    if sort_order:
        if sort_order == "last_modified":
            sort_mapping = {"remote_modified": {"order": "desc"}}
        elif sort_order == "trends":
            sort_mapping = [{"average_rating": {"order": "desc"}}, {"dataset_count": {"order": "desc"}}]
        else:
            sort_mapping = {"dataset_title.keyword": {"order": sort_order}}
    else:
        sort_mapping = {}

    if query_string:
        filters = [
            {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "org_title": {
                                    "query": query_string,
                                    "operator": "OR",
                                    "fuzziness": "AUTO",
                                    "boost": "2",
                                }
                            }
                        },
                        {
                            "match": {
                                "org_description": {
                                    "query": query_string,
                                    "boost": "0.5",
                                }
                            }
                        },
                    ],
                }
            }
        ]
        query = {"bool": {"must": filters}}
        # query = {"match": {"org_title": {"query": query_string, "operator": "AND"}}}
    else:
        query = {"bool": {"must": {"range": {"dataset_count": {"gt": 0}}}}}

    resp = es_client.search(
        index="organizations",
        query=query,
        size=size,
        from_=paginate_from,
        sort=sort_mapping,
    )
    return HttpResponse(json.dumps(resp["hits"]))


def more_like_this(request):
    id = request.GET.get("q", None)
    if id:
        query = {
            "more_like_this": {
                "like": [{"_index": "dataset", "_id": id}],
                "min_term_freq": 0,
                "max_query_terms": 10,
                "min_doc_freq": 0,
            }
        }
        resp = es_client.search(index="dataset", query=query)
        return HttpResponse(json.dumps(resp["hits"]))


def org_user_count(organization):
    user_count = (
        DatasetAccessModelRequest.objects.filter(
            Q(access_model_id__dataset_id__catalog__organization=organization.id),
            Q(access_model_id__dataset__status__exact="PUBLISHED"),
        )
        .values_list("user")
        .distinct()
        .count()
    )
    return user_count


def org_dataset_count(organization):
    dataset = Dataset.objects.filter(
        Q(status__exact="PUBLISHED"),
        Q(catalog__organization=organization.id),
    ).count()
    return dataset


def org_average_rating(organization):
    pub_datasets = Dataset.objects.filter(
        Q(status__exact="PUBLISHED"),
        Q(catalog__organization=organization.id),
    )
    count = 0
    rating = 0
    for dataset in pub_datasets:
        dataset_rating = get_average_rating(dataset)
        if dataset_rating > 0:
            count = count + 1
            rating = rating + dataset_rating
    return rating / count if rating else 0


def reindex_organizations():
    obj = OrganizationCreateRequest.objects.all()
    for org_obj in obj:
        update_organization_index(org_obj)


def update_organization_index(org_obj):
    if org_obj.status == "APPROVED":
        doc = {
            "id": org_obj.id,
            "org_title": org_obj.title,
            "org_description": org_obj.description,
            "homepage": org_obj.homepage,
            "contact": org_obj.contact_email,
            "type": org_obj.organization_types,
            "dpa_name": org_obj.dpa_name,
            "dpa_email": org_obj.dpa_email,
            "dpa_designation": org_obj.dpa_designation,
            "state": org_obj.state.name if org_obj.state else "",
            "parent": org_obj.parent.id if org_obj.parent else "",
            "dpa_phone": org_obj.dpa_phone,
            "dpa_tid": org_obj.ogd_tid,
            "sub_type": org_obj.organization_subtypes,
            "address": org_obj.address,
            "status": org_obj.status,
            "issued": org_obj.issued,
            "modified": org_obj.modified,
            "logo": org_obj.logo.name,
            "dataset_count": org_dataset_count(org_obj),
            "user_count": org_user_count(org_obj),
            "average_rating": org_average_rating(org_obj),
        }
        # Check if Org already exists.
        resp = es_client.exists(index="organizations", id=org_obj.id)
        if resp:
            # Delete the Org.
            resp = es_client.delete(index="organizations", id=org_obj.id)
        #     # print(resp["result"])
        # Index the Organization.
        resp = es_client.index(index="organizations", id=org_obj.id, document=doc)
        print(resp["result"], org_obj.id)
        # return resp["result"]


def reindex_data():
    dataset_obj = Dataset.objects.filter(status="PUBLISHED")
    for datasets in dataset_obj:
        resp = index_data(datasets)
        if resp == "created":
            print("Dataset_id --", datasets.id)
        else:
            print("Re-indexing failed!")
