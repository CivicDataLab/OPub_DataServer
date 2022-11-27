import jwt

from django.conf import settings
from django.http import HttpResponse

from .models import DataRequest
from dataset_api.enums import SubscriptionUnits


def user_key(group, request):
    token = request.GET.get("token")
    group = group.split("||")
    if len(group) > 1:
        request_id = group[1]
    else:
        if token:
            try:
                token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return HttpResponse("Authentication failed", content_type="text/plain")
            except IndexError:
                return HttpResponse("Token prefix missing", content_type="text/plain")
            if token_payload:
                request_id = token_payload.get("data_request")
        else:
            request_id = request.path.split("/")[3]

    data_request_instance = DataRequest.objects.get(pk=request_id)
    user = data_request_instance.user
    dam_request = data_request_instance.dataset_access_model_request

    return user + "||" + str(dam_request.id)


def rate_per_user(group, request):
    token = request.GET.get("token")
    group = group.split("||")
    if len(group) > 1:
        request_id = group[1]
    else:
        if token:
            try:
                token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return HttpResponse("Authentication failed", content_type="text/plain")
            except IndexError:
                return HttpResponse("Token prefix missing", content_type="text/plain")
            if token_payload:
                request_id = token_payload.get("data_request")
        else:
            request_id = request.path.split("/")[3]

    data_request_instance = DataRequest.objects.get(pk=request_id)
    dam = (
        data_request_instance.dataset_access_model_request.access_model.data_access_model
    )
    rate_limit = dam.rate_limit
    rate_limit_unit = dam.rate_limit_unit

    if dam.type == "OPEN":
        # user = "Unlimited"
        return None  # No rate limit -- UNLIMITED usage.
    else:
        if rate_limit_unit == "SECOND":
            return str(rate_limit) + "/" + rate_limit_unit.lower()[0]
        elif rate_limit_unit == "MINUTE":
            return str(rate_limit) + "/" + rate_limit_unit.lower()[0]
        elif rate_limit_unit == "HOUR":
            return str(rate_limit) + "/" + rate_limit_unit.lower()[0]
        elif rate_limit_unit == "DAY":
            return str(rate_limit) + "/" + rate_limit_unit.lower()[0]
        elif rate_limit_unit == "WEEK":
            return str(rate_limit) + "/7d"
        elif rate_limit_unit == "MONTH":
            return str(rate_limit) + "/30d"
        elif rate_limit_unit == "QUARTER":
            return str(rate_limit) + "/92d"
        else:
            return str(rate_limit) + "/365d"


def quota_per_user(group, request):
    token = request.GET.get("token")
    group = group.split("||")
    if len(group) > 1:
        request_id = group[1]
    else:
        if token:
            try:
                token_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return HttpResponse("Authentication failed", content_type="text/plain")
            except IndexError:
                return HttpResponse("Token prefix missing", content_type="text/plain")
            if token_payload:
                request_id = token_payload.get("data_request")
        else:
            request_id = request.path.split("/")[3]

    data_request_instance = DataRequest.objects.get(pk=request_id)
    dam = (
        data_request_instance.dataset_access_model_request.access_model.data_access_model
    )
    quota_limit = dam.subscription_quota
    quota_limit_unit = dam.subscription_quota_unit
    if dam.type == "OPEN":
        return None  # No rate limit -- UNLIMITED usage.
    else:
        if quota_limit_unit == SubscriptionUnits.DAILY:
            return str(quota_limit) + "/" + quota_limit_unit.lower()[0]
        elif quota_limit_unit == SubscriptionUnits.WEEKLY:
            return str(quota_limit) + "/7d"
        elif quota_limit_unit == SubscriptionUnits.MONTHLY:
            return str(quota_limit) + "/30d"
        elif quota_limit_unit == SubscriptionUnits.QUARTERLY:
            return str(quota_limit) + "/92d"
        else:
            return str(quota_limit) + "/365d"
