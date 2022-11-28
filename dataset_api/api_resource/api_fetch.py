import mimetypes
import os

from django.http import HttpResponse, JsonResponse

from dataset_api.models.DataAccessModel import DataAccessModel
from dataset_api.models.Resource import Resource

import pandas as pd
import requests
import os
from io import StringIO
import genson
import json


def parse_schema(schema_dict, parent, schema):
    global count
    for key in schema_dict:
        if key == "required":
            continue
        print(key)
        if key == "items":
            print(count)
            count = count + 1
            print(count)
            schema.append(
                {
                    "key": parent + str(count) if parent == "items" else parent,
                    "format": "array",
                    "description": "",
                    "parent": "",
                    "array_field": "items" + str(count),
                }
            )
            parse_schema(schema_dict["items"], key, schema)
            continue
        if key == "type":
            continue

        if key == "properties":
            schema.append(
                {
                    "key": parent + str(count) if parent == "items" else parent,
                    "format": "json",
                    "description": "",
                    "parent": "",
                    "array_field": "",
                }
            )
            parse_schema(schema_dict["properties"], parent, schema)
            continue
        if "type" in schema_dict[key] and schema_dict[key]["type"] not in [
            "array",
            "object",
        ]:
            schema.append(
                {
                    "key": key,
                    "format": "string",
                    "description": "",
                    "parent": parent + str(count) if parent == "items" else parent,
                    "array_field": "",
                }
            )
        else:
            parse_schema(schema_dict[key], key, schema)


def preview(request, resource_id):

    resp = fetchapi(resource_id)
    print ('---*************************************************************', resp)
    if resp["Success"] == False:
        return JsonResponse(resp, safe=False)

    print (resp['response_type'])

    if resp["response_type"] == "json":
        context = {
            "Success": True,
            "data": resp["data"],
            "response_type": resp["response_type"],
        }
        return JsonResponse(context, safe=False)
    if resp["response_type"] == "csv":
        context = {
            "Success": True,
            "data": resp["data"].head().to_dict("records"),
            "response_type": resp["response_type"],
        }
        return JsonResponse(context, safe=False)
    context = {
            "Success": True,
            "data": resp["data"],
            "response_type": resp["response_type"],
        }
    return JsonResponse(context, safe=False)



def schema(request, resource_id):

    resp = fetchapi(resource_id)
    if resp["Success"] == False:
        return JsonResponse(resp, safe=False)

    if resp["response_type"] == "json":
        builder = genson.SchemaBuilder()
        jsondata = json.loads(resp["data"])
        builder.add_object(jsondata)
        schema_dict = builder.to_schema()
        schema_dict = schema_dict.get("properties", {})
        schema = []
        global count
        count = 0
        print("------asadasf", schema_dict)
        parse_schema(schema_dict, "", schema)
        context = {
            "Success": True,
            "schema": schema,
            "response_type": resp["response_type"],
        }
        return JsonResponse(context, safe=False)
    if resp["response_type"] == "csv":
        df = resp["data"]
        schema_list = pd.io.json.build_table_schema(df, version=False)
        schema_list = schema_list.get("fields", [])
        schema = []
        print(schema_list)
        for each in schema_list:
            schema.append(
                {
                    "key": each["name"],
                    "format": each["type"],
                    "description": "",
                    "parent": "",
                    "array_field": "",
                }
            )
        context = {
            "Success": True,
            "schema": schema,
            "response_type": resp["response_type"],
        }
        print ('----a', context)
        return JsonResponse(context, safe=False)

    context = {
            "Success": False,
            "error": "couldn't read schema",
            "response_type": resp["response_type"],
        }
    return JsonResponse(context, safe=False)




def fetchapi(resource_id):

    try:
        res_model = Resource.objects.get(pk=resource_id)

        base_url = res_model.apidetails.api_source.base_url
        url_path = res_model.apidetails.url_path
        headers = res_model.apidetails.api_source.headers
        auth_loc = res_model.apidetails.api_source.auth_loc
        auth_type = res_model.apidetails.api_source.auth_type
        response_type = res_model.apidetails.response_type
        request_type = res_model.apidetails.request_type
        api_params = res_model.apidetails.apiparameter_set.all()

        format_loc = res_model.apidetails.format_loc
        format_key = res_model.apidetails.format_key
        target_format = res_model.apidetails.default_format

        param = {}
        header = {}
        if auth_loc == "HEADER":
            if auth_type == "TOKEN":
                auth_token = res_model.apidetails.api_source.auth_token
                auth_token_key = res_model.apidetails.api_source.auth_token_key
                header = {auth_token_key: auth_token}
            elif auth_type == "CREDENTIAL":
                # [{key:username,value:dc, description:desc},{key:password,value:pass, description:desc}]
                auth_credentials = res_model.apidetails.api_source.auth_credentials
                uname_key = auth_credentials[0]["key"]
                uname = auth_credentials[0]["value"]
                pwd_key = auth_credentials[1]["key"]
                pwd = auth_credentials[1]["value"]
                header = {uname_key: uname, pwd_key: pwd}
        if auth_loc == "PARAM":
            if auth_type == "TOKEN":
                auth_token = res_model.apidetails.api_source.auth_token
                auth_token_key = res_model.apidetails.api_source.auth_token_key
                param = {auth_token_key: auth_token}
            elif auth_type == "CREDENTIAL":
                auth_credentials = res_model.apidetails.api_source.auth_credentials
                uname_key = auth_credentials[0]["key"]
                uname = auth_credentials[0]["value"]
                pwd_key = auth_credentials[1]["key"]
                pwd = auth_credentials[1]["value"]
                param = {uname_key: uname, pwd_key: pwd}

        if format_key and format_key != "":
            if format_loc == "HEADER":
                header.update({format_key: target_format})
            if format_loc == "PARAM":
                param.update({format_key: target_format})

        print ('-----apiparams',api_params)
        for each in api_params:
            print ('---each',each)
            param.update({each.key: each.default})
        
        base_url = base_url.strip()
        url_path = url_path.strip()
        print ('----fetch', header, param, base_url, url_path)
        if request_type == "GET":
            try:
                api_request = requests.get(
                    base_url + url_path, headers=header, params=param, verify=True
                )
            except:
                api_request = requests.get(
                    base_url + url_path, headers=header, params=param, verify=False
                )
        elif request_type == "POST":
            api_request = requests.post(
                base_url + url_path, headers=header, params=param, body={}, verify=False
            )
        elif request_type == "PUT":
            api_request = requests.put(
                base_url + url_path, headers=header, params=param, verify=False
            )

        api_response = api_request.text
        response_type = (
            target_format if target_format and target_format != "" else response_type
        )

        
        if response_type == "json":
            context = {
                "Success": True,
                "data": api_response,
                "response_type": response_type,
            }
            return context
        if response_type == "csv":
            csv_data = StringIO(api_response)
            data = pd.read_csv(csv_data, sep=",")
            context = {"Success": True, "data": data, "response_type": response_type}
            return context

        if response_type not in ["json", "csv"]:
            try:
        	    context = {
            		"Success": True,
            		"data": api_request.json(),
            		"response_type": "json",
        		}
		         return context
            except:
            	try:

            		csv_data = StringIO(api_response)
            		data = pd.read_csv(csv_data, sep=",")
            		context = {"Success": True, "data": data, "response_type": "csv"}
					return context
				except:
					context = {"Success": True, "data": api_response, "response_type": "text"}
					return context

        print (response_type, '----', api_response)
        context = {
                "Success": True,
                "data": api_response,
                "response_type": response_type,
            }
        return context

    except Exception as e:
        raise e
        context = {"Success": False, "error": str(e)}
        return context
