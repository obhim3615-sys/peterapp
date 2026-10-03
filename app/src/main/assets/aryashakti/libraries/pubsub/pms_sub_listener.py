# services/pms_pubsub_listener.py

import logging

from payment import models
from django.conf import settings
from libraries.pubsub.pubsub_listener import PubSubListener
from app_farm.utils.helper import addVerification

logger = logging.getLogger(__name__)


class PMSPubSubListener(PubSubListener):

    def process_message(self, payload: dict):

        event = payload.get("event")
        event_id = payload.get("eventId")
        status = payload.get("status")

        logger.info(
            "Processing PMS Event | event=%s | event_id=%s",
            event,
            event_id
        )

        if event != "CUSTOMER_ACCOUNT_VALIDATION":
            logger.info(
                "Ignoring PMS event type=%s",
                event
            )
            return

        customer_details = payload.get(
            "customerDetails",
            {}
        )

        transaction_details = payload.get(
            "transactionDetails",
            {}
        )

        pams_account_id = customer_details.get(
            "pamsAccountId"
        )

        if not pams_account_id:
            logger.warning(
                "No pamsAccountId found in payload"
            )
            return

        try:

            bank_account = (
                models.UserBankAccount.objects
                .select_related("user")
                .get(
                    pams_account_id=pams_account_id
                )
            )

        except models.UserBankAccount.DoesNotExist:

            logger.warning(
                "Bank account not found for pams_account_id=%s",
                pams_account_id
            )

            return

        transaction_status = transaction_details.get(
            "transactionStatus"
        )

        transaction_result = transaction_details.get(
            "status"
        )

        # SUCCESS CASE
        if (
            status == "COMPLETED"
            and transaction_status == "COMPLETED"
            and transaction_result == "success"
        ):

            addVerification(
                user=bank_account.user,
                doc_type=settings.BANK_ACCOUNT_DOCUMENT_ID,
                doc_id=bank_account.id,
                type="payment_bankaccountvalidation_request",
                status=1
            )

            logger.info(
                "Bank account verified successfully "
                "for pams_account_id=%s",
                pams_account_id
            )

            return

        # FAILURE CASE
        addVerification(
            user=bank_account.user,
            doc_type=settings.BANK_ACCOUNT_DOCUMENT_ID,
            doc_id=bank_account.id,
            type="payment_bankaccountvalidation_request",
            status=4
        )

        logger.warning(
            "Bank verification failed "
            "for pams_account_id=%s",
            pams_account_id
        )