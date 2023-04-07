import datetime

from graphql import GraphQLError
from dataset_api.models import DataRequest
from dataset_api.enums import ValidationUnits


def dam_request_validity(func):
    def inner(*args, **kwargs):
        data_request_id = kwargs["data_request_id"]
        data_request_instance = DataRequest.objects.get(pk=data_request_id)
        dataset_access_request_status = (
            data_request_instance.dataset_access_model_request.status
        )
        dam_type = (
            data_request_instance.dataset_access_model_request.access_model.data_access_model.type
        )
        if dam_type != "OPEN":
            # Check if the dataset model request is APPROVED
            if dataset_access_request_status == "APPROVED":
                validation = (
                    data_request_instance.dataset_access_model_request.access_model.data_access_model.validation
                )
                validation_unit = (
                    data_request_instance.dataset_access_model_request.access_model.data_access_model.validation_unit
                )
                approval_date = data_request_instance.dataset_access_model_request.modified

                if validation_unit == ValidationUnits.DAY:
                    validation_deadline = approval_date + datetime.timedelta(
                        days=validation
                    )
                    if datetime.datetime.now(datetime.timezone.utc) > validation_deadline:
                        raise GraphQLError("The data access model is no longer valid.")
                elif validation_unit == ValidationUnits.WEEK:
                    validation_deadline = approval_date + datetime.timedelta(
                        weeks=validation
                    )
                    if datetime.datetime.now(datetime.timezone.utc) > validation_deadline:
                        raise GraphQLError("The data access model is no longer valid.")
                elif validation_unit == ValidationUnits.MONTH:
                    validation_deadline = approval_date + datetime.timedelta(
                        days=(30 * validation)
                    )
                    if datetime.datetime.now(datetime.timezone.utc) > validation_deadline:
                        raise GraphQLError("The data access model is no longer valid.")
                elif validation_unit == ValidationUnits.YEAR:
                    validation_deadline = approval_date + datetime.timedelta(
                        days=(365 * validation)
                    )
                    if datetime.datetime.now(datetime.timezone.utc) > validation_deadline:
                        raise GraphQLError("The data access model is no longer valid.")
                return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    return inner
