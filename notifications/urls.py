from django.urls import path

from .views import (
    ListNotificationsView,
    MarkAllNotificationsReadView,
    MarkNotificationReadView,
)

urlpatterns = [
    path("", ListNotificationsView.as_view(), name="list-notifications"),
    path(
        "<int:pk>/mark-read/",
        MarkNotificationReadView.as_view(),
        name="mark-notification-read",
    ),
    path(
        "mark-all-read/",
        MarkAllNotificationsReadView.as_view(),
        name="mark-all-notifications-read",
    ),
]
