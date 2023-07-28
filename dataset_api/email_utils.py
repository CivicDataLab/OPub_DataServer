import json
import requests
from django.conf import settings
from dataset_api.models import Dataset, Organization

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
    dataset_instance = Dataset.objects.get(pk=contact_info.get("dataset_id"))
    body = {
        "actor": contact_info.get("user"),
        "action": "contact_provider",
        "tgt_obj": contact_info.get("org_id"),
        "tgt_group": "Entity",
        "extras": {"category": contact_info.get("category"), "desc": contact_info.get("desc"),
                   "dataset_id": contact_info.get("dataset_id"), "dataset_title": dataset_instance.title},
    }
    headers = {}
    response = requests.request("POST", email_url, json=body, headers=headers)
    response_json = response.text
    return response_json


def contact_consumer_notif(contact_info):
    org_instance = Organization.objects.get(pk=contact_info.get("org_id"))
    body = {
        "actor": contact_info.get("user"),
        "action": "contact_consumer",
        "tgt_obj": contact_info.get("org_id"),
        "tgt_group": "Entity",
        "extras": {"entity_title": org_instance.title, "subject": contact_info.get("subject"),
                   "msg": contact_info.get("msg"), "consumers": contact_info.get("consumers")},
    }
    headers = {}
    response = requests.request("POST", email_url, json=body, headers=headers)
    response_json = response.text
    return response_json


def remind_dpa_notif(contact_info, request):
    dataset_instance = request.access_model.dataset
    body = {
        "actor": contact_info.get("user"),
        "action": "remind_dpa_for_data_access",
        "tgt_obj": dataset_instance.id,
        "tgt_group": "Dataset",
        "extras": {"req_date": contact_info.get("req_date"), "consumer": contact_info.get("consumer"),
                   "dpa": contact_info.get("dpa"), "dataset_id": dataset_instance.id,
                   "dataset_title": dataset_instance.title},
    }
    headers = {}
    response = requests.request("POST", email_url, json=body, headers=headers)
    response_json = response.text
    return response_json
