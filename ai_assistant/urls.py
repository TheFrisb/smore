from django.urls import path

from .views import SendMessageToAiView

urlpatterns = [
    path("send-message/", SendMessageToAiView.as_view(), name="send-message"),
]
