import mimetypes
import os
import magic

from django.http import HttpResponse

from dataset_api.models.Policy import Policy


def download(request, policy_id):
    policy = Policy.objects.get(pk=policy_id)
    file_path = policy.file.path
    if len(file_path):
        mime_type = magic.from_file(file_path, mime=True)
        response = HttpResponse(policy.file, content_type=mime_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
    else:
        response = HttpResponse("file doesnt exist", content_type='text/plain')
    return response
