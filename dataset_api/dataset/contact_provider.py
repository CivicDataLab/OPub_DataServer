import json
from ..email_utils import contact_provider_notif
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import requests

from django.conf import settings
cms_url = settings.CMS_URL
idp_url = settings.IDP_URL

'''
Trigger mail for contact_provider
'''
@csrf_exempt
def contact_provider(request):
    
    post_data = json.loads(request.body.decode("utf-8"))
    
    # store the contact details in strapi
    try:
        contact_url = 'contacts' if cms_url[-1] == '/' else '/contacts' 
        body = {
            "Name": post_data.get("user"),
            "Email": post_data.get("Name"),
            "Category": post_data.get("category"),
            "Description": post_data.get("desc"),
            "DatasetURL": idp_url + post_data.get("dataset_id", ""),
        }
        headers= {
            'Content-Type': 'application/json',
          }        
        response = requests.post(cms_url + contact_url,  data= json.dumps(body), headers= headers, verify=False)
        print(response.text)
    except Exception as e:
        print(str(e))
        return JsonResponse({"Success": False, "error": str(e)}, safe=False)
    
    
    # Send email notification to the user for subscribing to dataset.
    if post_data.get("category") in ["Feedback", "Providers"]:
        try:
            contact_provider_notif(post_data)
            return JsonResponse({"Success": True}, safe=False)
        except Exception as e:
            print(str(e))
    else:
        return JsonResponse({"Success": True}, safe=False)

    return JsonResponse({"Success": False}, safe=False)


@csrf_exempt
def subscribe(request):
    
    post_data = json.loads(request.body.decode("utf-8"))
    
    try:
        subscribe_url = 'subscriptions' if cms_url[-1] == '/' else '/subscriptions' 
        body = {
            "subscriber_email": post_data.get("email")
        }
        headers= {
            'Content-Type': 'application/json',
          }
        response = requests.post(cms_url + subscribe_url,  data= json.dumps(body), headers= headers, verify=False)
        print(response.text)
        if response.status_code == 200:
            return JsonResponse({"Success": True}, safe=False)
        else:
            return JsonResponse({"Success": False, "error": response.text}, safe=False)
        
    except Exception as e:
        print (str(e))
        return JsonResponse({"Success": False, "error": str(e)}, safe=False)
        
