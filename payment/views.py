from django.http import JsonResponse
from instamojo_wrapper import Instamojo

from dataset_api.dataset_access_model.enums import PAYMENTTYPES
from dataset_api.models import DatasetAccessModelRequest


def initiate_payment(request, dataset_access_model_request_id):
    dam_request = DatasetAccessModelRequest.objects.get(pk=dataset_access_model_request_id)
    if dam_request.status != "APPROVED":
        return JsonResponse({"error": "Request not approved yet"})
    if dam_request.access_model.payment_type == PAYMENTTYPES.FREE:
        return JsonResponse({"error": "Request not approved yet"})
    api = Instamojo(api_key="test_f2db7702b40ba69fc5e2771fc3d",
                    auth_token="test_4963e0b1921ccd8c44190cb6d9b", endpoint='https://test.instamojo.com/api/1.1/')

    # Create a new Payment Request
    response = api.payment_request_create(
        amount=dam_request.access_model.payment,
        purpose=f'Payment for {dam_request.access_model.title}',
        send_email=False,
        email="foo@example.com",
        redirect_url="http://dev.idp.civicdatalab.in/handle_redirect"
    )

    return JsonResponse(response)
