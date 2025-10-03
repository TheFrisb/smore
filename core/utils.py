def is_request_from_switzerland(request):
    return request.session.get("is_switzerland", False)
