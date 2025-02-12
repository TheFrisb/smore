def get_ip_addr(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", None)

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR", None)

    if ip is None:
        ip = ""
    return ip


def get_user_agent(request):
    return request.META.get("HTTP_USER_AGENT", "")
