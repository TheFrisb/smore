import logging

from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from facebook.services.facebook_pixel import FacebookPixel

logger = logging.getLogger(__name__)


# Create your views here.
class ContactPixelEventApiView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            fb_pixel = FacebookPixel(request)
            fb_pixel.contact()
        except Exception as e:
            logger.error(f"Error sending Contact Facebook Pixel event: {e}")

        return Response(status=HTTP_204_NO_CONTENT)


class LeadPixelEventApiView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            fb_pixel = FacebookPixel(request)
            fb_pixel.subscribe()
        except Exception as e:
            logger.error(f"Error sending Subscribe Facebook Pixel event: {e}")
        return Response(status=HTTP_204_NO_CONTENT)
