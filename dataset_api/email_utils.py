import json
import requests
from django.conf import settings

email_url = settings.EMAIL_URL


def dataset_approval_notif(username, dataset_id, org_id):
    body = {
        "actor": username,
        "action": "Approved",
        "tgt_obj": dataset_id,
        "tgt_group": "Dataset",
        "extras": {"tgt_org": org_id, "action_name": "publish dataset"},
    }
    headers = {}
    response = requests.request("POST", email_url, json=body, headers=headers)
    response_json = response.text
    return response_json


def org_create_notif(username, org_obj):
    body = {
        "actor": username,
        "action": "Created",
        "tgt_obj": org_obj.title,
        "tgt_group": "Entity",
        "extras": {"tgt_org": org_obj.id, "action_name": "register entity"},
    }
    headers = {}
    response = requests.request("POST", email_url, json=body, headers=headers)
    response_json = response.text
    return response_json


def register_dpa_notif(username, org_obj):
    body = {
        "actor": username,
        "action": "Added DPA",
        "tgt_obj": org_obj.title,
        "tgt_group": "to Entity",
        "extras": {
            "tgt_org": org_obj.id,
            "action_name": "add dpa",
            "dpa_email": org_obj.dpa_email,
            "entity_email": org_obj.contact_email,
        },
    }
    headers = {}
    response = requests.request("POST", email_url, json=body, headers=headers)
    response_json = response.text
    return response_json


def register_dp_notif(username, org_req_obj):
    body = {
        "actor": username,
        "action": "Added DP",
        "tgt_obj": org_req_obj.organization.title,
        "tgt_group": "to Entity",
        "extras": {
            "tgt_org": org_req_obj.organization.id,
            "action_name": "add dp",
            "dp_email": org_req_obj.user_email,
        },
    }
    headers = {}
    response = requests.request("POST", email_url, json=body, headers=headers)
    response_json = response.text
    return response_json


def data_access_approval_notif(username, dam_req_obj):
    body = {
        "actor": username,  # Approval User
        "action": "Approved",
        "tgt_obj": dam_req_obj.access_model.dataset.title,  # Dataset Title
        "tgt_group": "Access for Dataset",
        "extras": {
            "tgt_dataset": dam_req_obj.access_model.dataset.id,
            "action_name": "approve data access request",
            "requestor": dam_req_obj.user,
        },
    }
    headers = {}
    response = requests.request("POST", email_url, json=body, headers=headers)
    response_json = response.text
    return response_json
