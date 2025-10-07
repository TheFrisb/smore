from django.db import models


def is_request_from_switzerland(request):
    return request.session.get("is_switzerland", False)


class BaseInternalModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
