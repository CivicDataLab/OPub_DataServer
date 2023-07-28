import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from dataset_api.models import DatasetAccessModelRequest
from payment.decorators import rest_validate_token


@csrf_exempt
@rest_validate_token
def reset_token(request, dam_request_id, username):
    try:
        dam_request = DatasetAccessModelRequest.objects.get(id=dam_request_id, user=username)
    except DatasetAccessModelRequest.DoesNotExist as e:
        return JsonResponse({"success": False, "message": "Data Access Model Request doesnt exist"})
    dam_request.token_time = datetime.datetime.now()
    dam_request.save()
    return JsonResponse({"success": True})
