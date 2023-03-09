import json
from ..email_utils import contact_provider_notif

'''
Trigger mail for contact_provider
'''

def contact_provider(request):
    
    post_data = json.loads(request.body.decode("utf-8"))
    
    # Send email notification to the user for subscribing to dataset.
    try:
        contact_provider_notif(post_data)
    except Exception as e:
        print(str(e))