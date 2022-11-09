from .models import DataRequest


def per_user(group, request):
    request_id = request.path.split("/")[3]
    data_request_instance = DataRequest.objects.get(pk=request_id)
    rate_limit = data_request_instance.dataset_access_model_request.access_model.data_access_model.rate_limit
    rate_limit_unit = data_request_instance.dataset_access_model_request.access_model.data_access_model.rate_limit_unit
    limit = str(rate_limit) + "/" + rate_limit_unit.lower()[0]
    return limit

def my_key(group, request):
    request_id = request.path.split("/")[3]
    data_request_instance = DataRequest.objects.get(pk=request_id)
    user = data_request_instance.user
    return user