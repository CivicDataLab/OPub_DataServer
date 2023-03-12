import json
from ..email_utils import contact_provider_notif
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse

'''
Trigger mail for contact_provider
'''
@csrf_exempt
def contact_provider(request):
    
    post_data = json.loads(request.body.decode("utf-8"))
    
    # Send email notification to the user for subscribing to dataset.
    try:
        contact_provider_notif(post_data)
        return JsonResponse({"Success": True}, safe=False)
    except Exception as e:
        print(str(e))

    return JsonResponse({"Success": False}, safe=False)
