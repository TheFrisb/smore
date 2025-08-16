from django.urls import path

from .views import LogCreateView

urlpatterns = [
    path("", LogCreateView.as_view(), name="log-create"),
]
