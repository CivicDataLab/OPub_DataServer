import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from payment.decorators import rest_validate_token
from ..email_utils import remind_dpa_notif
from ..models import DatasetAccessModelRequest, OrganizationCreateRequest

'''
Trigger mail for remind_dpa
'''


@csrf_exempt
@rest_validate_token
def remind_dpa(request, username):
    post_data = json.loads(request.body.decode("utf-8"))
    print('-------------------', post_data)
    post_data['user'] = username
    request_ids = post_data['request_ids']
    try:
        for request_id in request_ids:
            data_access_model_request_instance = DatasetAccessModelRequest.objects.get(
                id=request_id
            )
            post_data['req_date'] = data_access_model_request_instance.issued.strftime("%m/%d/%Y, %H:%M:%S")
            post_data['consumer'] = data_access_model_request_instance.user
            org_id = data_access_model_request_instance.access_model.dataset.catalog.organization.id
            post_data['dpa'] = OrganizationCreateRequest.objects.get(organization_ptr_id=org_id).dpa_email
            # Send email notification to the user for subscribing to dataset.
            remind_dpa_notif(post_data, data_access_model_request_instance)
        return JsonResponse({"Success": True}, safe=False)
    except Exception as e:
        print(str(e))
        return JsonResponse({"Success": False, "error": str(e)}, safe=False)
