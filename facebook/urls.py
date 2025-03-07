from django.urls import path

from facebook.views import (
    ContactPixelEventApiView,
    LeadPixelEventApiView,
    SendViewContentPixelEventApiView,
)

app_name = "facebook"
urlpatterns = [
    path(
        "pixel/events/contact/",
        ContactPixelEventApiView.as_view(),
        name="contact_pixel_event",
    ),
    path(
        "pixel/events/lead/",
        LeadPixelEventApiView.as_view(),
        name="lead_pixel_event",
    ),
    path(
        "pixel/events/view-content/",
        SendViewContentPixelEventApiView.as_view(),
        name="view_content_pixel_event",
    ),
]
