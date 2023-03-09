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
        "action": "register_entity",
        "tgt_obj": org_obj.id,
        "tgt_group": "Entity",
        "extras": {"entity_title": org_obj.title, "entity_email": org_obj.contact_email},
    }
    headers = {}
    response = requests.request("POST", email_url, json=body, headers=headers)
    response_json = response.text
    return response_json


def register_dpa_notif(username, org_obj):
    body = {
        "actor": username,
        "action": "add_dpa",
        "tgt_obj": org_obj.id,
        "tgt_group": "Entity",
        "extras": {
            "entity_title": org_obj.title,
            "dpa_email": org_obj.dpa_email,
            "dpa_name": org_obj.dpa_name,
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
        "action": "add_dp",
        "tgt_obj": org_req_obj.organization.id,
        "tgt_group": "Entity",
        "extras": {
            "entity_title": org_req_obj.organization.title,
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
        "action": "approve_data_access",
        "tgt_obj": dam_req_obj.access_model.dataset.id,  # Dataset Title
        "tgt_group": "Dataset",
        "extras": {
            "dataset_title": dam_req_obj.access_model.dataset.title,
            "consumer": dam_req_obj.user,
        },
    }
    headers = {}
    response = requests.request("POST", email_url, json=body, headers=headers)
    response_json = response.text
    return response_json


def subscribe_notif(username, dataset_obj, action):
    body = {
        "actor": username,
        "action": action,
        "tgt_obj": dataset_obj.id,
        "tgt_group": "Dataset",
        "extras": {"dataset_title": dataset_obj.title},
    }
    headers = {}
    response = requests.request("POST", email_url, json=body, headers=headers)
    response_json = response.text
    return response_json


def contact_provider_notif(contact_info):
    body = {
        "actor": contact_info.user,
        "action": "contact_provider",
        "tgt_obj": contact_info.org_id,
        "tgt_group": "Entity",
        "extras": {"category": contact_info.category, "desc": contact_info.desc, "dataset_id": contact_info.dataset_id, "dataset_title":contact_info.dataset_title },
    }
    headers = {}
    response = requests.request("POST", email_url, json=body, headers=headers)
    response_json = response.text
    return response_json
