import json

from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from instamojo_wrapper import Instamojo

from dataset_api.dataset_access_model.enums import PAYMENTTYPES
from dataset_api.models import DatasetAccessModelRequest
from payment.decorators import rest_validate_token
from payment.models import Transaction
from DatasetServer import settings

@csrf_exempt
@rest_validate_token
def initiate_payment(request, dataset_access_model_request_id, username):
    dam_request = DatasetAccessModelRequest.objects.get(pk=dataset_access_model_request_id)
    if dam_request.status != "PAYMENTPENDING":
        return JsonResponse({"error": "Request not approved yet"})
    if dam_request.access_model.payment_type == PAYMENTTYPES.FREE:
        return JsonResponse({"error": "This is not a Free model"})
    api = Instamojo(api_key="test_f2db7702b40ba69fc5e2771fc3d",
                    auth_token="test_4963e0b1921ccd8c44190cb6d9b", endpoint='https://test.instamojo.com/api/1.1/')
    payment_purpose = f'Payment for {dam_request.access_model.title}'
    # Create a new Payment Request
    response = api.payment_request_create(
        amount=dam_request.access_model.payment,
        purpose=payment_purpose,
        send_email=False,
        email=username,
        redirect_url=("%s/handle_redirect" % settings.DEPLOYMENT_DOMAIN),
        allow_repeated_payments=False
    )
    transaction = Transaction(payment_request_id=response['payment_request']['id'], user=username, status="INITIATED",
                              access_request=dam_request, payment_purpose=payment_purpose)
    transaction.save()

    return JsonResponse(response)


@csrf_exempt
@rest_validate_token
def process_payment(request, username):
    post_data = json.loads(request.body.decode("utf-8"))
    payment_id = post_data['payment_id']
    payment_status = post_data['payment_status']
    payment_request_id = post_data['payment_request_id']
    api = Instamojo(api_key="test_f2db7702b40ba69fc5e2771fc3d",
                    auth_token="test_4963e0b1921ccd8c44190cb6d9b", endpoint='https://test.instamojo.com/api/1.1/')
    response = api.payment_request_payment_status(str(payment_request_id), str(payment_id))
    if payment_status != response['payment_request']['payment']['status']:
        return HttpResponseForbidden("Status mismatch")

    transaction = Transaction.objects.get(payment_request_id=payment_request_id)
    if payment_status == 'Credit':
        transaction.access_request.status = 'APPROVED'
        transaction.access_request.save()
    transaction.payment_id = payment_id
    transaction.status = payment_status
    transaction.save()
    return JsonResponse({"success": True})
