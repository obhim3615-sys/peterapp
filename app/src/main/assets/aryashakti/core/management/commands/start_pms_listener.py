# payments/management/commands/start_pms_listener.py

from django.core.management.base import BaseCommand
from django.conf import settings

from libraries.pubsub.pms_sub_listener import PMSPubSubListener


class Command(BaseCommand):
    help = "Start PMS PubSub Listener"

    def handle(self, *args, **kwargs):
        listener = PMSPubSubListener(
            subscription_id=settings.PUBSUB_PAYMENT_SUBSCRIPTION,
        )

        listener.start()