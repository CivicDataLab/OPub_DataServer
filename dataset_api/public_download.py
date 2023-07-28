import mimetypes
import os
import magic
import copy, requests

from django.http import HttpResponse
from django.conf import settings

from django.core.files.storage import default_storage

cms_url = settings.CMS_URL


def download(request, file_path):

    print ('--------path', file_path)
    file_path = '/' + file_path
    if  default_storage.exists(file_path):
        file = default_storage.open(file_path, 'rb').read()
        file_copy = copy.deepcopy(file)
        mime_type = magic.from_buffer(file_copy, mime=True)
       
        
        response = HttpResponse(file, content_type=mime_type)
    else:
        response = HttpResponse("file doesnt exist", content_type='text/plain')
    return response


def cmsdownload(request, file_path):

    print ('--------path', file_path)
    cms_base_url = cms_url
    file_path = file_path if (file_path[0] == '/' or cms_base_url[-1] == '/') else '/' + file_path
    print ('--------path1', file_path)
    
    try:
       file =  requests.get(cms_base_url + file_path,  verify=False)
       
       file_copy = copy.deepcopy(file.content)
       mime_type = magic.from_buffer(file_copy, mime=True)
       print ('--------mime', mime_type)
       
       response = HttpResponse(file.content, content_type=mime_type)
       response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
       
    except Exception as e:
       response = HttpResponse(str(e), content_type='text/plain')
       
    return response
    

