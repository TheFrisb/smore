from django.urls import path

from .views import SendMessageToAiView, GetSentMessagesCount

urlpatterns = [
    path("send-message/", SendMessageToAiView.as_view(), name="send-message"),
    path("can-send/", GetSentMessagesCount.as_view(), name="can-send-message"),
]
