from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from facebook.services.facebook_pixel import FacebookPixel


# Create your views here.
class ContactPixelEventApiView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        fb_pixel = FacebookPixel(request)
        fb_pixel.contact()
        return Response(status=HTTP_204_NO_CONTENT)
