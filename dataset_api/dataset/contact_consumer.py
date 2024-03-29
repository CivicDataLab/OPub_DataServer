import json
from ..email_utils import contact_consumer_notif
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse

'''
Trigger mail for contact_consumer
'''
@csrf_exempt
def contact_consumer(request):
    
    post_data = json.loads(request.body.decode("utf-8"))
    print ('-------------------', post_data) 
    # Send email notification to the user for subscribing to dataset.
    try:
        contact_consumer_notif(post_data)
        return JsonResponse({"Success": True}, safe=False)
    except Exception as e:
        print(str(e))
        return JsonResponse({"Success": False, "error": str(e)}, safe=False)
