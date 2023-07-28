from django.urls import path

from payment.views import initiate_payment

urlpatterns = [
    path('initiatepayment/<int:dataset_access_model_request_id>', initiate_payment)
]
