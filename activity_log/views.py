from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from dataset_api.utils import log_activity
from payment.decorators import rest_validate_token


# Create your views here.

@csrf_exempt
@rest_validate_token
def login_logout_activity(request, action: str, username):
    action = action.upper()
    log_activity(
        ip=request.META['REMOTE_ADDR'],
        username=username,
        verb=action,
    )
    return JsonResponse({"success": True})
