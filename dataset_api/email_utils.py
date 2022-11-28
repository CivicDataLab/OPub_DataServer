import json
import requests

email_url = "https://mailer.idp.civicdatalab.in/send-email/backgroundtasks"


def dataset_approval_notif(username, dataset_id, org_id):
    body = {
        "actor": username,
        "action": "Approved",
        "tgt_obj": dataset_id,
        "tgt_group": "Dataset",
        "extras": {"tgt_org": org_id},
    }
    headers = {}
    response = requests.request("POST", email_url, json=body, headers=headers)
    response_json = response.text
    return response_json