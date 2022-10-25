def get_client_ip(request):
    x_forwarded_for = request.context.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.context.META.get('REMOTE_ADDR')
    return ip
