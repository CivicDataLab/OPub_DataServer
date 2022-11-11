import mimetypes
import os

from django.http import HttpResponse, JsonResponse

from dataset_api.models.DataAccessModel import DataAccessModel
from dataset_api.models.Resource import Resource

import pandas as pd
import requests
import os
from io import StringIO


def preview(request, resource_id):

    res_model = Resource.objects.get(pk=resource_id)

    base_url = res_model["api_details"]["api_source"]["base_url"]
    url_path = res_model["api_details"]["url_path"]
    headers = res_model["api_details"]["api_source"]["headers"]
    auth_loc = res_model["api_details"]["api_source"]["auth_loc"]
    auth_type = res_model["data"]["resource"]["api_details"]["api_source"]["auth_type"]
    response_type = res_model["data"]["resource"]["api_details"]["response_type"]
    param = {}
    header = {}
    if auth_loc == "HEADER":
        if auth_type == "TOKEN":
            auth_token = res_model["data"]["resource"]["api_details"]["api_source"][
                "auth_token"
            ]
            header = {"access_token": auth_token}
        elif auth_type == "CREDENTIAL":
            # [{key:username,value:dc, description:desc},{key:password,value:pass, description:desc}]
            auth_credentials = res_model["data"]["resource"]["api_details"][
                "api_source"
            ][
                "auth_credentials"
            ]  # - uname pwd
            uname_key = auth_credentials[0]["key"]
            uname = auth_credentials[0]["value"]
            pwd_key = auth_credentials[1]["key"]
            pwd = auth_credentials[1]["value"]
            header = {uname_key: uname, pwd_key: pwd}
    if auth_loc == "PARAM":
        if auth_type == "TOKEN":
            auth_token = res_model["data"]["resource"]["api_details"]["api_source"][
                "auth_token"
            ]
            param = {"access_token": auth_token}
        elif auth_type == "CREDENTIAL":
            auth_credentials = res_model["data"]["resource"]["api_details"][
                "api_source"
            ][
                "auth_credentials"
            ]  # - uname pwd
            uname_key = auth_credentials[0]["key"]
            uname = auth_credentials[0]["value"]
            pwd_key = auth_credentials[1]["key"]
            pwd = auth_credentials[1]["value"]
            param = {uname_key: uname, pwd_key: pwd}

    try:

        try:
            api_request = requests.get(
                base_url + url_path, headers=header, params=param, verify=True
            )
        except:
            api_request = requests.get(
                base_url + url_path, headers=header, params=param, verify=False
            )
        api_response = api_request.text
        if response_type == "JSON":
            context = {"Success": True, "data": api_response}
            return JsonResponse(context, safe=False)
        if response_type == "CSV":
            csv_data = StringIO(api_response)
            data = pd.read_csv(csv_data, sep=";")
            context = {"Success": True, "data": data.head().to_dict("records")}
            return JsonResponse(context, safe=False)
    except Exception as e:
        context = {"Success": False, "error": str(e)}
        return JsonResponse(context, safe=False)
