# services/pubsub_listener.py

import json
import logging
from google.cloud import pubsub_v1
import google.auth

logger = logging.getLogger(__name__)


class PubSubListener:
    """
    Google Pub/Sub Subscriber using Application Default Credentials (ADC)

    Required IAM:
        roles/pubsub.subscriber

    Usage:
        listener = PubSubListener(
            project_id="my-project",
            subscription_id="payment-events-sub"
        )
        listener.start()
    """

    def __init__(self, subscription_id):

        _, project_id = google.auth.default()

        self.project_id = project_id
        self.subscription_id = subscription_id

        self.subscriber = pubsub_v1.SubscriberClient()

        self.subscription_path = self.subscriber.subscription_path(
            self.project_id,
            self.subscription_id
        )

    def process_message(self, payload: dict):
        """
        Override this method or implement business logic here.
        """

        logger.info(
            "Received event: %s",
            payload
        )

        # Example:
        # event_id = payload.get("event_id")
        # transaction_id = payload.get("transaction_id")
        # payment_status = payload.get("status")

    def callback(self, message):
        """
        Called automatically by Pub/Sub when a message arrives.
        """

        try:
            payload = json.loads(
                message.data.decode("utf-8")
            )

            logger.info(
                "PubSub Message Received | message_id=%s",
                message.message_id
            )

            self.process_message(payload)

            message.ack()

            logger.info(
                "PubSub Message Acked | message_id=%s",
                message.message_id
            )

        except Exception as exc:
            logger.exception(
                "PubSub Processing Failed | message_id=%s | error=%s",
                message.message_id,
                str(exc)
            )

            message.nack()

    def start(self):
        """
        Start listening indefinitely.
        """

        logger.info(
            "Listening to subscription: %s",
            self.subscription_path
        )

        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=self.callback,
        )

        try:
            streaming_pull_future.result()

        except KeyboardInterrupt:
            logger.info("Stopping PubSub listener...")

            streaming_pull_future.cancel()

        except Exception:
            logger.exception("PubSub listener crashed")

            streaming_pull_future.cancel()

            raise