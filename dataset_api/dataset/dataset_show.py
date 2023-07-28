import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse

from typing import Iterable


from dataset_api.search import index_data

from dataset_api.decorators import validate_token, auth_user_by_org
from dataset_api.enums import DataType
from dataset_api.models import (
    Catalog,
    Organization,
    OrganizationCreateRequest,
    Resource,
    FileDetails,
    APIDetails,
    Dataset,
    DatasetAccessModel, DatasetAccessModelRequest,
)
from dataset_api.utils import dataset_slug, get_average_rating
from DatasetServer import settings


@csrf_exempt
def dataset_show(request, dataset_id):
    
    dataset_obj = Dataset.objects.get(pk=dataset_id)
    try:
        data = {
        "dataset_title": dataset_obj.title,
        "dataset_description": dataset_obj.description,
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
        "url": settings.BASE_DOMAIN + dataset_slug(dataset_obj.id),
        "highlights": dataset_obj.highlights or [],
        "download_count": dataset_obj.download_count,
        "average_rating": get_average_rating(dataset_obj),
        "hvd_rating": dataset_obj.hvd_rating,  
        }
        
        
        # geo, sector and tags
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
        data["geography"] = dataset_geography
        data["sector"] = dataset_sector
        data["tags"] = dataset_tag
        
        
        # org details
        catalog_instance = Catalog.objects.get(id=dataset_obj.catalog_id)
        org_instance = Organization.objects.get(id=catalog_instance.organization_id)
        data["org_title"] = org_instance.title
        data["org_description"] = org_instance.description
        
        # resource and dam details
        resource_instance = Resource.objects.filter(dataset_id=dataset_obj.id)
        resource_info = []
        for resources in resource_instance:
            # Checks based on datasets_type.
            if dataset_obj.dataset_type == DataType.API.value:
                api_details_obj = APIDetails.objects.get(resource_id=resources.id)
                format = (api_details_obj.response_type)
            elif dataset_obj.dataset_type == DataType.FILE.value:
                file_details_obj = FileDetails.objects.get(resource_id=resources.id)
                format = (file_details_obj.format)
            else:
                continue           
            resource_info.append({"title":resources.title, "description": resources.description, "format": format})
        data["resources"] = resource_info


        dam_instances = DatasetAccessModel.objects.filter(dataset=dataset_obj)
        dam_info= []
        for dam in dam_instances:
            dam_info.append({"title": dam.data_access_model.title, "type": dam.data_access_model.type })
        data["data_access_model"] = dam_info
        

        context = {"Success": True, "data": data}
    except Exception as e:
        context = {"Success": False, "error": str(e)}
        
    return JsonResponse(context, safe=False)
