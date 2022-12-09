import magic
import mimetypes

def check_ext(file_object):
    ext_type = mimetypes.guess_type(file_object.path)[0]
    return ext_type

def check_mime_type(file_object):
    mime_type = magic.from_buffer(file_object.file.read(), mime=True)
    return mime_type

def file_validation(file_object):
    ext_type = check_ext(file_object)
    print("ext--", ext_type)
    mime_type = check_mime_type(file_object)
    print("mime--", mime_type)
    if ext_type and mime_type:
        if ext_type == mime_type:
            return mime_type
        else:
            return None
    else:
        return None