from django.contrib.auth.models import AbstractUser

from core.models import BaseInternalModel


# Create your models here.
class User(BaseInternalModel, AbstractUser):
    pass
