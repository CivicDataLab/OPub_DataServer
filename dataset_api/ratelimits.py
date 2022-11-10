from .models import DataRequest
from dataset_api.enums import SubscriptionUnits


def user_key(group, request):
    request_id = request.path.split("/")[3]
    data_request_instance = DataRequest.objects.get(pk=request_id)
    user = data_request_instance.user
    dam_id = data_request_instance.dataset_access_model_request.access_model.data_access_model
    return user + "||" + str(dam_id.id)


def rate_per_user(group, request):
    request_id = request.path.split("/")[3]
    data_request_instance = DataRequest.objects.get(pk=request_id)
    rate_limit = (
        data_request_instance.dataset_access_model_request.access_model.data_access_model.rate_limit
    )
    rate_limit_unit = (
        data_request_instance.dataset_access_model_request.access_model.data_access_model.rate_limit_unit
    )
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
    request_id = request.path.split("/")[3]
    data_request_instance = DataRequest.objects.get(pk=request_id)
    quota_limit = (
        data_request_instance.dataset_access_model_request.access_model.data_access_model.subscription_quota
    )
    quota_limit_unit = (
        data_request_instance.dataset_access_model_request.access_model.data_access_model.subscription_quota_unit
    )
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
