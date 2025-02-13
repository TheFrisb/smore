from django.urls import path

from facebook.views import ContactPixelEventApiView, LeadPixelEventApiView

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
]
