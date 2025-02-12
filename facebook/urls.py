from django.urls import path

from facebook.views import ContactPixelEventApiView

urlpatterns = [
    path(
        "pixel/events/contact/",
        ContactPixelEventApiView.as_view(),
        name="contact_pixel_event",
    )
]
