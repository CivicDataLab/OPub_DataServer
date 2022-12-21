import mimetypes
import os

from django.http import HttpResponse, JsonResponse

from dataset_api.models.DataAccessModel import DataAccessModel
from dataset_api.models.Resource import Resource
from dataset_api.utils import json_keep_column

import pandas as pd
import requests
import os
from io import StringIO
import genson
import json
import xmltodict
import dicttoxml



def preview(request, resource_id):
    
    row_count = request.GET.get("row_count", None)
    cols      = request.GET.get("fields", None)
    data_params    = dict(request.GET.items())

    api_data_params = {}
    for key, value in api_data_params.items():
        if key not in ["row_count", "fields"]:
            api_data_params[key] = value
  
    
    res_model = Resource.objects.get(pk=resource_id)
    res_type = "api"
    if hasattr(res_model, "filedetails") and res_model.filedetails != None:
        res_type = "file"
        
    cols     = cols.split(",") if cols != None else []
    print('------------cols', cols)      
    keep_cols = list(res_model.resourceschema_set.filter(id__in=cols).values_list('key', flat=True))
    keep_cols_path = list(res_model.resourceschema_set.filter(id__in=cols).values_list('path', flat=True))
    print('------------keepcols', keep_cols)
    print('------------keepcolspath', keep_cols_path)        
    
    resp = fetchapi(resource_id, api_data_params)
    # print("----------dat fetched", resp)
    if resp["Success"] == False:
        return JsonResponse(resp, safe=False)
    # print(resp["response_type"])


    if resp["response_type"].lower() == "json":
        data = resp["data"]
        data = json_keep_column(data, keep_cols, keep_cols_path)
        data = pd.json_normalize(data)
        data = data if res_type == "api" else data.head(int(row_count) if row_count != None else 0) 
        data = data.to_dict("records")
        context = {
            "Success": True,
            "data":  data,
            "response_type": resp["response_type"],
        }
        return JsonResponse(context, safe=False)
    
    if resp["response_type"].lower() == "csv":
        data = resp["data"]
        data = data.loc[:, data.columns.isin(keep_cols)]
        data = data if res_type == "api" else data.head(int(row_count) if row_count != None else 0)      
        data = data.to_string() if len(data.columns) > 0 and len(data) > 0 else ""
        context = {
            "Success": True,
            "data": data, #.to_dict("records"),
            "response_type": resp["response_type"],
        }
        return JsonResponse(context, safe=False)
    
    
    if resp["response_type"].lower() == "xml":
        data = xmltodict.parse(resp["data"])
        data = json_keep_column(data, keep_cols, keep_cols_path)
        data = pd.json_normalize(data)
        data = data if res_type == "api" else data.head(int(row_count) if row_count != None else 0)
        data = dicttoxml.dicttoxml(data.to_dict("records")).decode("utf-8") 
        context = {
            "Success": True,
            "data": data, 
            "response_type": resp["response_type"],
        }
        return JsonResponse(context, safe=False)    
    
    context = {
        "Success": True,
        "data": resp["data"],
        "response_type": resp["response_type"],
    }
    return JsonResponse(context, safe=False)


def fetchapi(resource_id, api_data_params):
    
    res_model = Resource.objects.get(pk=resource_id)
    res_type = "api"
    if hasattr(res_model, "filedetails") and res_model.filedetails != None:
        res_type = "file"
        
        
    if  res_type == "file":
        
        try:
            file_path = res_model.filedetails.file.path
            file_format = res_model.filedetails.format  

            
            if file_format.lower() == "json":
                with open(file_path, "r") as fp:
                    data = json.load(fp)
            if file_format.lower() == "csv":
                data = pd.read_csv(file_path)
            if file_format.lower() == "xml":
                with open(file_path) as xmlFile:
                    data = xmlFile.read()
            if file_format.lower() not in ["json", "csv", "xml"]:
                with open(file_path) as xmlFile:
                    data = xmlFile.read()
              
            context = {"Success": True, "data": data, "response_type": file_format}
            return context
            
        except Exception as e:
            context = {"Success": False, "error": str(e)}
            return context
            
        
    if  res_type == "api":
        
        try:
            res_model = Resource.objects.get(pk=resource_id)

            base_url = res_model.apidetails.api_source.base_url
            url_path = res_model.apidetails.url_path
            headers = res_model.apidetails.api_source.headers
            auth_loc = res_model.apidetails.api_source.auth_loc
            auth_type = res_model.apidetails.api_source.auth_type
            response_type = res_model.apidetails.response_type
            request_type = res_model.apidetails.request_type
            print(res_model.apidetails.apiparameter_set.all())
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

            print("-----apiparams", api_params)
            for each in api_params:
                print("---each", each)
                param.update({each.key: each.default})    
            param.update(api_data_params)

            base_url = base_url.strip()
            url_path = url_path.strip()
            print(
                "----fetch", header, param, base_url, url_path, response_type, target_format
            )
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

            if response_type.lower() in ["json", "xml"]:
                context = {
                    "Success": True,
                    "data": api_response,
                    "response_type": response_type,
                }
                return context
            if response_type.lower() == "csv":
                csv_data = StringIO(api_response)
                data = pd.read_csv(csv_data, sep=",")
                context = {"Success": True, "data": data, "response_type": response_type}
                return context

            print(response_type, "----", api_response)
            context = {
                "Success": True,
                "data": api_response,
                "response_type": response_type,
            }
            return context

        except Exception as e:
            context = {"Success": False, "error": str(e)}
            return context
