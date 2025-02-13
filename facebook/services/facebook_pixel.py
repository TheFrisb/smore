import logging
import uuid
from datetime import datetime
from hashlib import sha256

from django.conf import settings
from facebook_business import FacebookAdsApi
from facebook_business.adobjects.serverside.action_source import ActionSource
from facebook_business.adobjects.serverside.content import Content
from facebook_business.adobjects.serverside.custom_data import CustomData
from facebook_business.adobjects.serverside.event import Event
from facebook_business.adobjects.serverside.event_request import EventRequest
from facebook_business.adobjects.serverside.user_data import UserData

from facebook.utils import get_ip_addr, get_user_agent

logger = logging.getLogger(__name__)


class FacebookPixel:
    def __init__(self, request):
        self.dataset_id = settings.FACEBOOK_PIXEL_DATASET_ID
        self.request = request
        FacebookAdsApi.init(
            access_token=settings.FACEBOOK_PIXEL_ACCESS_TOKEN,
        )

    def send_event(self, event_name, custom_data=None):
        user_data = self.get_default_user_data()

        event_0 = Event(
            event_name="ViewContent",
            event_time=int(datetime.now().timestamp()),
            user_data=user_data,
            action_source=ActionSource.WEBSITE,
            event_source_url=self.extract_event_source_url(),
            event_id=uuid.uuid4().hex,
            custom_data=custom_data,
        )

        events = [event_0]
        event_request = EventRequest(
            events=events,
            pixel_id=settings.FACEBOOK_PIXEL_DATASET_ID,
            access_token=settings.FACEBOOK_PIXEL_ACCESS_TOKEN,
        )

        return event_request.execute()

    def view_content(self):
        event_response = self.send_event("ViewContent")
        logger.info(f"ViewContent event sent: {event_response}")

    def complete_registration(self):
        event_response = self.send_event("CompleteRegistration")
        logger.info(f"CompleteRegistration event sent: {event_response}")

    def lead(self):
        event_response = self.send_event("Lead")
        logger.info(f"Lead event sent: {event_response}")

    def contact(self):
        event_response = self.send_event("Contact")
        logger.info(f"Contact event sent: {event_response}")

    def initiate_checkout(self, product, total_price):
        custom_data = CustomData(
            value=float(total_price),
            currency="USD",
            content_type="product",
            content_ids=[product.id],
            num_items=1,
            contents=[
                Content(
                    product_id=product.id,
                    quantity=1,
                    item_price=float(total_price),
                    title=product.get_name_display(),
                )
            ],
        )

        event_response = self.send_event("InitiateCheckout", custom_data)

        logger.info(f"InitiateCheckout event sent: {event_response}")

    def purchase(self, product, total_price):
        custom_data = CustomData(
            value=float(total_price),
            currency="USD",
            content_type="product",
            content_ids=[product.id],
            num_items=1,
            contents=[
                Content(
                    product_id=product.id,
                    quantity=1,
                    item_price=float(total_price),
                    title=product.get_name_display(),
                )
            ],
        )

        event_response = self.send_event("Purchase", custom_data)

        logger.info(f"Purchase event sent: {event_response}")

    def subscribe(self):
        event_response = self.send_event("Subscribe")

        logger.info(f"Subscribe event sent: {event_response}")

    def extract_event_source_url(self):
        referrer = self.request.META.get("HTTP_REFERER", None)
        if referrer:
            return referrer
        return self.request.build_absolute_uri()

    def get_default_user_data(self):
        first_name = (
            sha256(self.request.user.first_name.encode()).hexdigest()
            if self.request.user.is_authenticated
            else None
        )
        last_name = (
            sha256(self.request.user.last_name.encode()).hexdigest()
            if self.request.user.is_authenticated
            else None
        )
        email = (
            sha256(self.request.user.email.encode()).hexdigest()
            if self.request.user.is_authenticated
            else None
        )
        external_id = (
            sha256(str(self.request.user.id).encode()).hexdigest()
            if self.request.user.is_authenticated
            else None
        )

        user_data = UserData(
            client_ip_address=get_ip_addr(self.request),
            client_user_agent=get_user_agent(self.request),
            fbc=self.request.COOKIES.get("_fbc", None),
            fbp=self.request.COOKIES.get("_fbp", None),
            first_name=first_name,
            last_name=last_name,
            email=email,
            external_id=external_id,
        )
        return user_data
